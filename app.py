from flask import Flask, request, abort
from linebot.models import TextMessage, AudioMessage, ImageMessage
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

#======langchain的函數庫==========
from langchain_community.chat_models import ChatPerplexity
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.prompts import ChatPromptTemplate
#======langchain的函數庫==========

#======python的函數庫==========
import tempfile, os
import json
import logging
import requests
import datetime
import openai
import time
import traceback
#======python的函數庫==========

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
    logger.info(f"Starting transcription for file: {file_path}")
    if not os.path.exists(file_path):
        error_msg = f"Error: The file {file_path} does not exist."
        logger.error(error_msg)
        return error_msg

    try:
        with open(file_path, "rb") as audio_file:
            transcript = openai.Audio.transcribe("whisper-1", audio_file)
        logger.info("Transcription successful.")
        return transcript.get("text", "無法獲取轉錄文本。")
    except openai.error.OpenAIError as e:
        error_msg = f"OpenAI API error during transcription: {str(e)}"
        logger.error(error_msg)
        return f"轉錄時發生錯誤：{str(e)}"
    except Exception as e:
        error_msg = f"Unexpected error during transcription: {str(e)}"
        logger.error(error_msg)
        return f"轉錄時發生意外錯誤：{str(e)}"

def GPT_response(text):
    # 接收回應
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini", 
        messages=[{"role": "user", "content": text}], 
        temperature=0.8, 
        max_tokens=500
    )
    logging.info(response)
    # 重組回應
    answer = response['choices'][0]['message']['content']
    return answer

def Preplexity_response(text):
    memory = ConversationBufferWindowMemory(k=5)
    #Preplexity chatbot
    chat = ChatPerplexity(
        temperature=0.2,
        model="llama-3.1-sonar-small-128k-online",
        pplx_api_key=Preplexity_API_KEY,
        max_tokens=2048,
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Be precise and concise. Please respond in traditional Chinese (繁體中文)."),
        ("human", "{input}")
    ])
    chain = ConversationChain(
        llm=chat,
        prompt=prompt,
        memory=memory
    )
    # payload = {
    #     "model": "llama-3.1-sonar-small-128k-online",
    #     "messages": [
    #         {
    #             "role": "system",
    #             "content": "Be precise and concise. Please respond in traditional Chinese (繁體中文)."
    #         },
    #         {
    #             "role": "user",
    #             "content": f"{text}"
    #         }
    #     ],
    #     "max_tokens": 4096,
    #     "temperature": 0.2,
    #     "top_p": 0.9,
    #     "return_citations": True,
    #     "search_domain_filter": ["perplexity.ai"],
    #     "return_images": True,
    #     "return_related_questions": True,
    #     "search_recency_filter": "month",
    #     "top_k": 0,
    #     "stream": False,
    #     "presence_penalty": 0,
    #     "frequency_penalty": 1
    # }
    # response = requests.request("POST", url, json=payload, headers=headers)
    # if response.status_code == 200:
    #     # Parse the JSON response
    #     result = response.json()
    #     # Extract the assistant's reply
    #     answer = result['choices'][0]['message']['content']
    #     #print("Assistant's reply:", answer)
    # else:
    #     logger.error("Error:", response.status_code, response.text)
    response = chain.predict(input=text)
    if response:
        return response
    else:
        logger.error("Error", response.text)

def Further_question(text):

    return None
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
        logger.error("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    return 'OK'


# 處理訊息
@handler.add(MessageEvent, message=(TextMessage, AudioMessage, ImageMessage))
def handle_message(event):
    memory = ConversationBufferWindowMemory(k=5)
    if isinstance(event.message, ImageMessage):
        logger.info("Received Image message")

        pass
    if isinstance(event.message, TextMessage):
        logger.info(f"Received message: {event.message.text}")
        msg = event.message.text
        try:
            # GPT_answer = GPT_response(msg)
            Preplexity_answer = Preplexity_response(msg)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(Preplexity_answer))
        except:
            logger.exception(traceback.format_exc())
            line_bot_api.reply_message(event.reply_token, TextSendMessage('你所使用的OPENAI API key額度可能已經超過，請於後台Log內確認錯誤訊息'))
    elif isinstance(event.message, AudioMessage):
        audio_content = line_bot_api.get_message_content(event.message.id)
        if not audio_content:
            logger.error("No audio content found.")
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text='無法獲取音訊內容。'))
            return
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.m4a') as tf:
                for chunk in audio_content.iter_content():
                    tf.write(chunk)
                tempfile_path = tf.name
                logger.info(f"Audio saved to temporary file: {tempfile_path}")
            
            msg = transcribe_audio(tempfile_path)
            if msg.startswith("Error"):
                raise Exception(msg)
            
            # Process the transcribed text
            Preplexity_answer = Preplexity_response(msg)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=Preplexity_answer))
        except Exception as e:
            logger.exception("Error handling audio message:")
            error_message = '處理您的音訊訊息時發生錯誤，請稍後再試。'
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=error_message))
        finally:
            # Clean up the temporary file
            if os.path.exists(tempfile_path):
                os.remove(tempfile_path)
                logger.info(f"Temporary file {tempfile_path} deleted.")

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
    logger.info(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port)
