import os
import base64
import io
from flask import Flask, render_template, request, jsonify
from google import genai
from google.genai import types
from PIL import Image

app = Flask(__name__)

# 无状态服务，不保存任何配置和文件

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/generate', methods=['POST'])
def generate():
    # 从请求中获取所有配置，不依赖服务器本地文件
    data = request.json
    
    api_key = data.get('api_key')
    base_url = data.get('base_url')
    model = data.get('model', 'gemini-2.5-flash-image')
    prompt = data.get('prompt')
    input_image_data = data.get('image') # Base64 string
    aspect_ratio = data.get('aspect_ratio')
    
    if not api_key:
        return jsonify({"error": "请在设置中配置 API Key"}), 401
    
    if not prompt:
        return jsonify({"error": "请输入提示词"}), 400

    try:
        # 配置 Client
        http_options = {}
        if base_url:
            http_options['base_url'] = base_url
            
        client = genai.Client(api_key=api_key, http_options=http_options if http_options else None)
        
        # 准备内容
        contents = [prompt]
        
        if input_image_data:
            try:
                if input_image_data.startswith('data:image'):
                    header, encoded = input_image_data.split(",", 1)
                    input_image_bytes = base64.b64decode(encoded)
                    image = Image.open(io.BytesIO(input_image_bytes))
                    contents.append(image)
            except Exception as e:
                return jsonify({"error": f"图片处理失败: {str(e)}"}), 400
        
        # 配置生成参数
        gen_config_args = {}
        
        if aspect_ratio:
            gen_config_args['image_config'] = types.ImageConfig(
                aspect_ratio=aspect_ratio
            )
            
        # 针对 Gemini 2.5/3 系列模型的特殊配置 (支持文本+图片多模态输出)
        # 2.5 Flash Image 和 3 Pro Image Preview 都是多模态模型，可以返回对话文本或思维链
        if 'gemini' in model.lower() or 'banana' in model.lower():
             gen_config_args['response_modalities'] = ['TEXT', 'IMAGE']

        config = types.GenerateContentConfig(**gen_config_args) if gen_config_args else None

        # 调用 Google API
        try:
            print(f"DEBUG: Calling Google API with model={model}, config={gen_config_args}")
            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=config
            )
            print("DEBUG: API Response Received")
        except Exception as api_err:
            print(f"DEBUG: API Call Failed: {api_err}")
            raise api_err
        
        # 处理结果
        generated_images_base64 = []
        generated_text = ""
        
        if response.candidates:
            print(f"DEBUG: Number of candidates: {len(response.candidates)}")
            for i, candidate in enumerate(response.candidates):
                if hasattr(candidate, 'content') and candidate.content and hasattr(candidate.content, 'parts'):
                    print(f"DEBUG: Candidate {i} has {len(candidate.content.parts)} parts")
                    for j, part in enumerate(candidate.content.parts):
                        # Debug print part attributes
                        print(f"DEBUG: Candidate {i} Part {j} attributes: {[d for d in dir(part) if not d.startswith('_')]}")
                        
                        # Extract Text
                        if hasattr(part, 'text') and part.text:
                            print(f"DEBUG: Found text in part {j}: {part.text[:50]}...")
                            generated_text += part.text + "\n"
                        
                        # Extract Thought (if separate from text in newer SDK versions, though usually in text)
                        if hasattr(part, 'thought') and part.thought:
                             print(f"DEBUG: Found thought in part {j}")
                             generated_text += f"[Thought]: {part.thought}\n"

                        # Extract Image
                        if hasattr(part, 'inline_data') and part.inline_data:
                            print(f"DEBUG: Found inline_data in part {j}")
                            # Google GenAI SDK v1.0+ usually returns raw bytes in part.inline_data.data
                            raw_data = part.inline_data.data
                            
                            if isinstance(raw_data, bytes):
                                # If it's already bytes, it's likely the raw image data
                                img_bytes = raw_data
                            else:
                                # If it's a string, it might be base64 encoded
                                try:
                                    img_bytes = base64.b64decode(raw_data)
                                except:
                                    # Fallback or error
                                    print(f"DEBUG: Failed to decode inline_data in part {j}")
                                    continue

                            # Encode to base64 string for frontend display
                            b64_str = base64.b64encode(img_bytes).decode('utf-8')
                            generated_images_base64.append(f"data:image/png;base64,{b64_str}")
                else:
                    print(f"DEBUG: Candidate {i} has no content or parts")
        else:
            print("DEBUG: No candidates in response")
        
        if not generated_images_base64 and not generated_text:
             print("DEBUG: No images and no text extracted")
             # Try to dump response for debugging if empty
             print(f"DEBUG: Full Response Dump: {response}")
             return jsonify({"error": "生成失败，未返回任何内容"}), 500

        print(f"DEBUG: Returning {len(generated_images_base64)} images and {len(generated_text)} chars of text")
        return jsonify({
            "images": generated_images_base64,
            "text": generated_text.strip()
        })

    except Exception as e:
        print(f"Error: {str(e)}") # Log error for debugging
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
