from flask import Flask, request, abort
from linebot.models import TextMessage, AudioMessage
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

#======python的函數庫==========
import tempfile, os
import json
import requests
import datetime
import openai
import time
import traceback
#======python的函數庫==========

app = Flask(__name__)
static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')
# Channel Access Token
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
# Channel Secret
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))
# OPENAI API Key初始化設定
openai.api_key = os.getenv('OPENAI_API_KEY')
# Preplexity API key
Preplexity_API_KEY = os.getenv('PREPLEXITY_API_KEY')
# Preplexity URL
url = "https://api.perplexity.ai/chat/completions"
# Set up the headers
headers = {
    "Authorization": f"Bearer {Preplexity_API_KEY}",
    "Content-Type": "application/json"
}

def transcribe_audio(file_path):
    if not os.path.exists(file_path):
        return f"Error: The file {file_path} does not exist."

    try:
        with open(file_path, "rb") as audio_file:
            transcript = openai.Audio.transcribe("whisper-1", audio_file)
        
        return transcript["text"]
    except Exception as e:
        return f"Error during transcription: {str(e)}"

def GPT_response(text):
    # 接收回應
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini", 
        messages=[{"role": "user", "content": text}], 
        temperature=0.6, 
        max_tokens=500
    )
    print(response)
    # 重組回應
    answer = response['choices'][0]['message']['content']
    return answer

def Preplexity_response(text):
    payload = {
        "model": "llama-3.1-sonar-small-128k-online",
        "messages": [
            {
                "role": "system",
                "content": "Be precise and concise. Please respond in traditional Chinese (繁體中文)."
            },
            {
                "role": "user",
                "content": f"{text}"
            }
        ],
        "max_tokens": "Optional",
        "temperature": 0.2,
        "top_p": 0.9,
        "return_citations": True,
        "search_domain_filter": ["perplexity.ai"],
        "return_images": True,
        "return_related_questions": True,
        "search_recency_filter": "month",
        "top_k": 0,
        "stream": False,
        "presence_penalty": 0,
        "frequency_penalty": 1
    }
    response = requests.request("POST", url, json=payload, headers=headers)
    if response.status_code == 200:
        # Parse the JSON response
        result = response.json()
        # Extract the assistant's reply
        answer = result['choices'][0]['message']['content']
        print("Assistant's reply:", answer)
    else:
        print("Error:", response.status_code, response.text)
    return answer

# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'


# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # Start from here 
    if isinstance(event.message, TextMessage):
        msg = event.message.text
        try:
            #GPT_answer = GPT_response(msg)
            Preplexity_answer = Preplexity_response(msg)
            #print(GPT_answer)
            print(Preplexity_answer)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(Preplexity_answer))
        except:
            print(traceback.format_exc())
            line_bot_api.reply_message(event.reply_token, TextSendMessage('你所使用的OPENAI API key額度可能已經超過，請於後台Log內確認錯誤訊息'))
    elif isinstance(event.message, AudioMessage):
        audio_content = line_bot_api.get_message_content(event.message.id)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tf:
            for chunk in audio_content.iter_content():
                tf.write(chunk)
            tempfile_path = tf.name
        msg = transcribe_audio(tempfile_path)
        try:
            #GPT_answer = GPT_response(msg)
            Preplexity_answer = Preplexity_response(msg)
            #print(GPT_answer)
            print(Preplexity_answer)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(Preplexity_answer))
        except:
            print(traceback.format_exc())
            line_bot_api.reply_message(event.reply_token, TextSendMessage('你所使用的OPENAI API key額度可能已經超過，請於後台Log內確認錯誤訊息'))

@handler.add(PostbackEvent)
def handle_message(event):
    print(event.postback.data)


@handler.add(MemberJoinedEvent)
def welcome(event):
    uid = event.joined.members[0].user_id
    gid = event.source.group_id
    profile = line_bot_api.get_group_member_profile(gid, uid)
    name = profile.display_name
    message = TextSendMessage(text=f'{name}歡迎加入')
    line_bot_api.reply_message(event.reply_token, message)
        
        
import os
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
