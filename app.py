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
# Perplexity chatbot prompt
chat = ChatPerplexity(
    temperature=0.2,
    model="llama-3.1-sonar-small-128k-online",
    pplx_api_key=Preplexity_API_KEY,
    max_tokens=2048,
)

prompt = ChatPromptTemplate.from_template("""
You are a helpful assistant. Please respond in traditional Chinese (繁體中文).

{history}

User: {input}
Assistant:
""")

conversation_with_summary = ConversationChain(
    llm=chat,
    prompt=prompt,
    memory=ConversationBufferWindowMemory(k=5),
    verbose=True,
    )

# Rephrase prompt
rephrase_llm = ChatOpenAI(
    openai_api_key=openai.api_key,
    model_name="gpt-4o-mini",
    temperature=0.8,
    max_tokens=2048,
)

rephrase_prompt = ChatPromptTemplate.from_template("""
根據以下對話歷史和用戶訊息，請重新表述用戶的問題，使其更清晰易懂。

對話歷史：
{history}

用戶訊息：{input}

重新表述後的用戶訊息：
""")

rephrase_conversation = ConversationChain(
    llm=rephrase_llm,
    prompt=rephrase_prompt,
    memory=ConversationBufferWindowMemory(k=5),
    verbose=True,
)

# Further questions prompt
further_prompt = ChatPromptTemplate.from_template("""
根據以下對話歷史和用戶訊息，請提供更多問題給用戶參考提問給 LLM ，讓用戶能知道還能問哪些問題。

對話歷史：
{history}

用戶訊息：{input}

推薦的問題：
""")

further_conversation = ConversationChain(
    llm=rephrase_llm,
    prompt=further_prompt,
    memory=ConversationBufferWindowMemory(k=5),
    verbose=True,
)

def transcribe_audio(file_path):
    """Transcribe Audio message to text for LLM."""
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
    """Generate GPT response."""
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

def Perplexity_response(text):
    """Perplexity response."""
    try:
        history = get_conversation_history(conversation_with_summary.memory)
        rephrased_text = rephrase_user_input(text, history)
        response = conversation_with_summary.invoke({"input": rephrased_text})
        logger.info(f"Response: {response}")
        further_questions = further_question(text, history)
        return response['response'], further_questions
    except Exception as e:
        logger.error(f"Error running the chain: {e}")
        return None, None

def rephrase_user_input(text, history):
    """Rephrase user message based on previous message so that LLM can better understand."""
    try:
        rephrase_response = rephrase_conversation.invoke({
            "history": history,
            "input": text
        })
        logger.info(f"Rephrased Input: {rephrase_response}")
        return rephrase_response['response']
    except Exception as e:
        logging.error(f"重新表述時出錯: {e}")
        return text  # 如果重新表述失敗，回傳原始輸入
    return None

def get_conversation_history(memory):
    """
    從 ConversationBufferWindowMemory 中提取對話歷史，並格式化為文本。
    
    :param memory: ConversationBufferWindowMemory 物件
    :return: 格式化後的對話歷史字符串
    """
    # 使用 load_memory_variables 來獲取 'history'
    memory_vars = memory.load_memory_variables({})
    return memory_vars.get('history', '')

def further_question(text, history):
    """Provide user further questions to ask."""
    try:
        further_questions_response = further_conversation.invoke({
            "history": history,
            "input": text
        })
        logger.info(f"Further questions: {further_questions_response}")
        return further_questions_response['response']
    except Exception as e:
        logger.error(f"Error: {e}")
        return text

def encode_image(image_path):
  # Function to encode the image
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')
    
def Image_recognize(image_base64):

    headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {openai.api_key}"
    }

    payload = {
    "model": "gpt-4o",
    "messages": [
        {
        "role": "user",
        "content": [
            {
            "type": "text",
            "text": "What’s in this image?"
            },
            {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{image_base64}"
            }
            }
        ]
        }
    ],
    "max_tokens": 300
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    return response.json()['choices'][0]['message']['content']

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
    msg = event.message.text
    try:
        # GPT_answer = GPT_response(msg)
        Preplexity_answer, questions = Perplexity_response(msg)
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
        
        msg = transcribe_audio(tempfile_path)
        if msg.startswith("Error"):
            raise Exception(msg)
        
        # Process the transcribed text
        Preplexity_answer, questions = Perplexity_response(msg)
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
    # Add your image processing logic here
    message_content = line_bot_api.get_message_content(event.message.id)
    image_base64 = base64.b64encode(message_content.content).decode('utf-8')
    description = Image_recognize(image_base64)
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
    message = TextSendMessage(text=f'{name}歡迎加入')
    line_bot_api.reply_message(event.reply_token, message)


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port)
