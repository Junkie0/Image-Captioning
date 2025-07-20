import numpy as np
import pickle
from tensorflow.keras.models import load_model, Model
from tensorflow.keras.applications import EfficientNetB0
from tensorflow.keras.applications.efficientnet import preprocess_input
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.layers import LSTM

def load_components():
    # Load tokenizer
    with open('model2/tokenizer.pkl', 'rb') as f:
        tokenizer = pickle.load(f)

    # Load model
    caption_model = load_model('model2/best_model.keras')

    # Disable CuDNN on all LSTM layers
    for layer in caption_model.layers:
        if isinstance(layer, LSTM):
            layer.use_cudnn = False

    # Automatically fetch max_length
    seq_input_shape = caption_model.inputs[1].shape
    max_length = int(seq_input_shape[1])

    # Rebuild EfficientNet feature extractor
    base_cnn = EfficientNetB0(weights='imagenet')
    feature_extractor = Model(
        inputs=base_cnn.inputs,
        outputs=base_cnn.layers[-2].output
    )

    return caption_model, tokenizer, feature_extractor, max_length


def prepare_image(image_path, feature_extractor):
    # Load and resize image
    img = load_img(image_path, target_size=(224, 224))
    x = img_to_array(img)
    x = np.expand_dims(x, axis=0)
    x = preprocess_input(x)
    features = feature_extractor.predict(x, verbose=0)
    return features


def generate_caption(model, features, tokenizer, max_length, max_words=10):
    in_text = 'startseq'
    word_count = 0

    while word_count < max_words:
        seq = tokenizer.texts_to_sequences([in_text])[0]
        seq = pad_sequences([seq], maxlen=max_length, padding='post')[0]
        yhat = model.predict([features, np.array([seq])], verbose=0)
        yhat_idx = np.argmax(yhat)
        word = tokenizer.index_word.get(yhat_idx)
        if not word or word == 'endseq':
            break
        in_text += ' ' + word
        word_count += 1

    # Remove 'startseq' and truncate
    words = in_text.split()[1:max_words+1]

    # Remove common starting conjunctions
    while words and words[0].lower() in ['and', 'but', 'or', 'so']:
        words.pop(0)

    # Capitalize the first word and join
    if words:
        words[0] = words[0].capitalize()
        caption = ' '.join(words)
        if not caption.endswith('.'):
            caption += '.'
    else:
        caption = "Couldn't generate a proper caption."

    return caption

