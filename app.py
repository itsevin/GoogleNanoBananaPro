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
        config = None
        if aspect_ratio:
            config = types.GenerateContentConfig(
                image_config=types.ImageConfig(
                    aspect_ratio=aspect_ratio
                )
            )

        # 调用 Google API
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=config
        )
        
        # 处理结果
        generated_images_base64 = []
        
        if response.candidates:
            for candidate in response.candidates:
                for part in candidate.content.parts:
                    if part.inline_data:
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
                                continue

                        # Encode to base64 string for frontend display
                        b64_str = base64.b64encode(img_bytes).decode('utf-8')
                        
                        # Verify it's a valid image (Optional but safer)
                        # try:
                        #     Image.open(io.BytesIO(img_bytes))
                        # except:
                        #     print("Warning: Generated data might not be a valid image")

                        generated_images_base64.append(f"data:image/png;base64,{b64_str}")

        if not generated_images_base64:
            return jsonify({"error": "生成失败，未返回图片数据", "details": str(response)}), 500
            
        return jsonify({"status": "success", "images": generated_images_base64})

    except Exception as e:
        # 捕获所有异常，包括 API 密钥错误等
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
