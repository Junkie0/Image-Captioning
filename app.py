from flask import Flask, request, render_template
import os
from utils import prepare_image, generate_caption, load_components

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Load model, tokenizer, etc.
caption_model, tokenizer, feature_extractor, max_length = load_components()


@app.route('/', methods=['GET', 'POST'])
def index():
    caption = ''
    filename = None
    if request.method == 'POST':
        file = request.files['file']  # Changed from 'image' to 'file'
        if file and file.filename:  # Added check for filename
            filename = file.filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            # Create upload directory if it doesn't exist
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

            file.save(filepath)
            features = prepare_image(filepath, feature_extractor)
            caption = generate_caption(caption_model, features, tokenizer, max_length)

    return render_template('index.html', caption=caption, filename=filename)


if __name__ == '__main__':  # Fixed the syntax
    app.run(debug=True)