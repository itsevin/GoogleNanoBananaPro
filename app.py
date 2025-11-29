import os
import json
import base64
import io
import time
from flask import Flask, render_template, request, jsonify
from google import genai
from google.genai import types
from PIL import Image

app = Flask(__name__)
CONFIG_FILE = 'config.json'
STATIC_FOLDER = 'static'
GENERATED_FOLDER = os.path.join(STATIC_FOLDER, 'generated')

os.makedirs(GENERATED_FOLDER, exist_ok=True)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "api_key": "",
        "base_url": "",
        "model_name": "gemini-2.5-flash-image"
    }

def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/config', methods=['GET'])
def get_config():
    return jsonify(load_config())

@app.route('/api/config', methods=['POST'])
def update_config():
    new_config = request.json
    current_config = load_config()
    current_config.update(new_config)
    save_config(current_config)
    return jsonify({"status": "success", "config": current_config})

@app.route('/api/generate', methods=['POST'])
def generate():
    config = load_config()
    api_key = config.get('api_key')
    base_url = config.get('base_url')
    default_model = config.get('model_name')
    
    if not api_key:
        return jsonify({"error": "API Key is missing. Please configure it in settings."}), 400

    data = request.json or request.form
    prompt = data.get('prompt')
    model = data.get('model', default_model)
    input_image_data = data.get('image') # Base64 string if provided
    aspect_ratio = data.get('aspect_ratio')
    
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400

    try:
        http_options = {}
        if base_url:
            http_options['base_url'] = base_url
            
        client = genai.Client(api_key=api_key, http_options=http_options if http_options else None)
        
        contents = [prompt]
        
        if input_image_data:
            # Handle base64 image
            if input_image_data.startswith('data:image'):
                header, encoded = input_image_data.split(",", 1)
                input_image_bytes = base64.b64decode(encoded)
                image = Image.open(io.BytesIO(input_image_bytes))
                contents.append(image)
        
        # Configure generation
        config = None
        if aspect_ratio:
            # Supports: "1:1", "3:4", "4:3", "9:16", "16:9"
            config = types.GenerateContentConfig(
                image_config=types.ImageConfig(
                    aspect_ratio=aspect_ratio
                )
            )

        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=config
        )
        
        generated_images = []
        
        # Check candidates
        if response.candidates:
            for candidate in response.candidates:
                for part in candidate.content.parts:
                    if part.inline_data:
                        image_data = part.inline_data.data
                        # Decode if necessary (usually bytes)
                        # The SDK might return raw bytes or base64 string depending on version
                        # But part.as_image() is a helper if available.
                        # In the snippet: image = part.as_image(); image.save(...)
                        
                        try:
                            # Try using SDK helper if available
                            if hasattr(part, 'as_image'):
                                img = part.as_image()
                            else:
                                # Manual decode
                                img_bytes = base64.b64decode(image_data)
                                img = Image.open(io.BytesIO(img_bytes))
                            
                            filename = f"gen_{int(time.time())}_{len(generated_images)}.png"
                            filepath = os.path.join(GENERATED_FOLDER, filename)
                            img.save(filepath)
                            generated_images.append(f"/static/generated/{filename}")
                        except Exception as e:
                            print(f"Error saving image part: {e}")

        if not generated_images:
            return jsonify({"error": "No image generated. Response might be blocked or empty.", "details": str(response)}), 500
            
        return jsonify({"status": "success", "images": generated_images})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
