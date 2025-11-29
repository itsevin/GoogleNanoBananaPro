# Google Nano Banana Pro Image Generator

基于 Python Flask 构建的 Web 应用程序，用于调用 Google Gemini (Nano Banana) 系列模型生成图片。

> 这个项目是我为了调用 DMXAPI 的第三方API创建的，非常好用，代码由 AI 生成

## 功能特点

1.  **多模式支持**：
    *   **文生图 (Text-to-Image)**：输入提示词生成高质量图片。
    *   **图生图 (Image-to-Image)**：上传参考图片并结合提示词生成新图片。
2.  **高度可配置**：
    *   支持在 Web 界面直接配置 `Base URL` (用于代理)、`API Key` 和 `Model Name`。
    *   配置信息持久化保存到本地 `config.json` 文件。
3.  **美观实用的 UI**：
    *   使用 Tailwind CSS 构建的现代化深色主题界面。
    *   实时预览上传图片。
    *   生成过程加载状态提示。
    *   一键下载生成的图片。
4.  **错误处理**：
    *   界面直观显示 API 调用错误信息，方便排查问题。

## 环境要求

*   Python 3.8+
*   Google Gemini API Key

## 安装与运行

1.  **安装依赖**

    ```bash
    pip install -r requirements.txt
    ```

2.  **配置**

    复制 `config.example.json` 为 `config.json` (可选，应用启动后也可在设置界面配置)。

3.  **启动应用**

    ```bash
    python app.py
    ```

4.  **访问界面**

    打开浏览器访问：`http://127.0.0.1:5000`

## 使用指南

1.  **首次设置**：
    *   点击右上角的齿轮图标 ⚙️ 打开设置。
    *   输入您的 Gemini API Key。
    *   如果需要代理，输入 Base URL (例如 `https://generativelanguage.googleapis.com` 或您的反代地址)。
    *   选择或输入模型名称 (默认 `gemini-2.5-flash-image`)。
    *   点击“保存”。

2.  **生成图片**：
    *   在左侧输入框填写提示词 (Prompt)。
    *   (可选) 点击虚线框上传一张参考图片。
    *   点击“生成图片”按钮。
    *   右侧将显示生成结果，点击“下载”即可保存到本地。

## 注意事项

*   生成的图片保存在 `static/generated/` 目录下。
*   请确保您的网络环境可以连接到 Google Gemini API (或配置了有效的 Base URL)。
