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
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.prompts import ChatPromptTemplate
#======langchain的函數庫==========


#======自訂的函數庫==========
from message_response import Message_Response
#======自訂的函數庫==========


#======python的函數庫==========
import tempfile, os
import base64
import requests
import logging
import openai
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
# openai.api_key = os.getenv('OPENAI_API_KEY')
# Preplexity API key
# Preplexity_API_KEY = os.getenv('PREPLEXITY_API_KEY')

# Initialize the Message_Response class
msg_response = Message_Response()

# global variable to store the questions
last_questions = []
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


# 處理文本訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    logger.info(f"Received message: {event.message.text}")
    if msg.isdigit() and msg == 0:
        msg_response.clear_memory()
    msg = event.message.text
    try:
        Preplexity_answer, questions = msg_response.Perplexity_response(msg)
        messages = [
            TextSendMessage(text=Preplexity_answer),
            TextSendMessage(text=f"更多可參考的問題：\n{questions}")
        ]
        line_bot_api.reply_message(event.reply_token, messages)
    except Exception as e:
        logger.exception(traceback.format_exc())
        line_bot_api.reply_message(
            event.reply_token, 
            TextSendMessage('你所使用的OPENAI API key額度可能已經超過，請於後台Log內確認錯誤訊息')
        )

# 處理音訊訊息
@handler.add(MessageEvent, message=AudioMessage)
def handle_audio_message(event):
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
        
        msg = msg_response.transcribe_audio(tempfile_path)
        if msg.startswith("Error"):
            raise Exception(msg)
        
        # Process the transcribed text
        Preplexity_answer, questions = msg_response.Perplexity_response(msg)
        messages = [
            TextSendMessage(text=Preplexity_answer),
            TextSendMessage(text=f"更多可參考的問題：\n{questions}")
        ]
        line_bot_api.reply_message(event.reply_token, messages)
    except Exception as e:
        logger.exception("Error handling audio message:")
        error_message = '處理您的音訊訊息時發生錯誤，請稍後再試。'
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=error_message))
    finally:
        # Clean up the temporary file
        if os.path.exists(tempfile_path):
            os.remove(tempfile_path)
            logger.info(f"Temporary file {tempfile_path} deleted.")

# 處理圖片訊息
@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    logger.info("Received Image message")
    message_content = line_bot_api.get_message_content(event.message.id)
    image_base64 = base64.b64encode(message_content.content).decode('utf-8')
    description = msg_response.Image_recognize(image_base64)
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f'圖片描述：{description}'))

@handler.add(PostbackEvent)
def handle_message(event):
    print(event.postback.data)


@handler.add(MemberJoinedEvent)
def welcome(event):
    uid = event.joined.members[0].user_id
    gid = event.source.group_id
    profile = line_bot_api.get_group_member_profile(gid, uid)
    name = profile.display_name
    message = TextSendMessage(text=f'{name}歡迎加入, 輸入0 來清除之前的歷史對話')
    line_bot_api.reply_message(event.reply_token, message)


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port)
