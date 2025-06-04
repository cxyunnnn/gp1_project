from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
from flask import Flask, render_template_string, request, Response
import os
import requests
from dotenv import load_dotenv

# === 初始化語言模型 ===
model_name = "fnlp/bart-base-chinese"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
summarizer = pipeline("summarization", model=model, tokenizer=tokenizer)

load_dotenv()
app = Flask(__name__)

# Azure Translator API
TRANSLATOR_KEY = os.getenv("AZURE_TRANSLATOR_KEY")
TRANSLATOR_LOCATION = os.getenv("AZURE_TRANSLATOR_REGION") or "eastUS"
TRANSLATOR_ENDPOINT = "https://api.cognitive.microsofttranslator.com"

# Azure Text Analytics API
TEXT_ANALYTICS_KEY = os.getenv("AZURE_TEXT_ANALYTICS_KEY")
TEXT_ANALYTICS_ENDPOINT = os.getenv("AZURE_TEXT_ANALYTICS_ENDPOINT")

# Azure Speech (TTS)
SPEECH_KEY = os.getenv("AZURE_TTS_KEY")
SPEECH_REGION = os.getenv("AZURE_TTS_REGION") or "eastasia"
SPEECH_ENDPOINT = f"https://{SPEECH_REGION}.tts.speech.microsoft.com"

HTML_TEMPLATE = """
<!doctype html>
<html>
<head>
    <title>新聞處理平台</title>
    <style>
        body {
            text-align: center;
            font-family: Arial, sans-serif;
            background-color: #f5f8ff;
        }
        textarea {
            border: 3px solid #007BFF;
            border-radius: 8px;
            font-size: 16px;
            font-weight: bold;
            padding: 10px;
            width: 80%;
        }
        select, button {
            font-size: 16px;
            padding: 8px 16px;
            margin: 10px;
        }
        pre {
            border: 3px solid #007BFF;
            border-radius: 8px;
            font-size: 16px;
            font-weight: bold;
            padding: 10px;
            width: 80%;
            background-color: white;
            color: black;
            white-space: pre-wrap;
            font-family: Arial, sans-serif;
            text-align: left;
            display: block;
            margin: 0 auto;
        }
    </style>
</head>
<body>
    <h1>📰 新聞處理平台</h1>
    <form method="POST">
        <textarea name="text" rows="12" placeholder="請貼上新聞內容">{{ original_text }}</textarea><br>
        <select name="translate_lang">
            <option value="zh-Hant">翻成中文</option>
            <option value="en">翻成英文</option>
        </select><br>
        <button name="action" value="translate" type="submit">翻譯</button>
        <button name="action" value="summary" type="submit">摘要</button>
        <button name="action" value="sentiment" type="submit">情感分析</button>
        <button name="action" value="clear" type="submit" style="background-color: #ff6666;">重整</button>
    </form>
    {% if result %}
    <h2>📘 處理結果：</h2>
    <pre id="resultText">{{ result }}</pre>
    <button onclick="speakText()">🔊 朗讀結果</button>
    {% endif %}

    <script>
    function speakText() {
        const text = document.getElementById("resultText").innerText;
        fetch("/speak", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: text })
        })
        .then(res => res.blob())
        .then(blob => {
            const audio = new Audio(URL.createObjectURL(blob));
            audio.play();
        });
    }
    </script>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    original_text = ""

    if request.method == "POST":
        text = request.form["text"]
        action = request.form["action"]
        original_text = "" if action == "clear" else text

        if action == "translate":
            to_lang = request.form["translate_lang"]
            headers = {
                'Ocp-Apim-Subscription-Key': TRANSLATOR_KEY,
                'Ocp-Apim-Subscription-Region': TRANSLATOR_LOCATION,
                'Content-type': 'application/json'
            }
            body = [{'text': text}]
            params = {'api-version': '3.0', 'to': to_lang}
            response = requests.post(TRANSLATOR_ENDPOINT + '/translate', params=params, headers=headers, json=body)
            try:
                translations = response.json()
                result = translations[0]['translations'][0]['text']
            except Exception as e:
                result = f"翻譯失敗：{e}\nAPI回傳內容：\n{response.text}"

        elif action == "summary":
            try:
                tokens = tokenizer.encode(text, truncation=False, add_special_tokens=False)
                token_len = len(tokens)

                if token_len < 30:
                    result = f"❗輸入內容太短（目前約 {token_len} tokens），請貼上更多內容。"
                elif token_len > 1024:
                    result = f"❗輸入內容太長（目前約 {token_len} tokens），請分段處理。"
                else:
                    summary = summarizer(text, max_length=128, min_length=30, do_sample=False)
                    result = summary[0]["summary_text"]
            except Exception as e:
                result = f"❌ 摘要處理失敗：{e}"

        elif action == "sentiment":
            headers = {
                "Ocp-Apim-Subscription-Key": TEXT_ANALYTICS_KEY,
                "Content-Type": "application/json"
            }
            documents = {"documents": [{"id": "1", "language": "en", "text": text}]}
            response = requests.post(TEXT_ANALYTICS_ENDPOINT + "/text/analytics/v3.1/sentiment", headers=headers, json=documents)
            if response.status_code == 200:
                sentiment_data = response.json()["documents"][0]
                sentiment = sentiment_data["sentiment"]
                scores = sentiment_data["confidenceScores"]
                result = f"情感分析結果：{sentiment}\n正向：{scores['positive']:.2f} 中性：{scores['neutral']:.2f} 負向：{scores['negative']:.2f}"
            else:
                result = "情感分析失敗：" + response.text

    return render_template_string(HTML_TEMPLATE, result=result, original_text=original_text)

@app.route("/speak", methods=["POST"])
def speak():
    text = request.json.get("text", "")
    headers = {
        "Ocp-Apim-Subscription-Key": SPEECH_KEY,
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": "audio-16khz-32kbitrate-mono-mp3"
    }
    ssml = f"""
    <speak version='1.0' xml:lang='zh-TW'>
        <voice xml:lang='zh-TW' xml:gender='Female' name='zh-TW-HsiaoYuNeural'>{text}</voice>
    </speak>
    """
    response = requests.post(
        SPEECH_ENDPOINT + "/cognitiveservices/v1",
        headers=headers,
        data=ssml.encode("utf-8")
    )
    return Response(response.content, mimetype="audio/mpeg")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
