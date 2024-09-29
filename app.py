from flask import Flask, request, abort, jsonify
from linebot.models import TextMessage, AudioMessage, ImageMessage
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

#======自訂的函數庫==========
from message_response import Message_Response
#======自訂的函數庫==========


#======python的函數庫==========
import tempfile, os, requests
import logging
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

def create_quick_reply_buttons(questions):
    buttons = []
    logger.info(questions)
    for index, question in enumerate(questions[:10], start=1):  # Limit to first 10 questions
        label = f"{index}"
        buttons.append(QuickReplyButton(
            action=MessageAction(label=label, text=str(index))
        ))
    return buttons

# 處理文本訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    global last_questions
    msg = event.message.text
    user_id = event.source.user_id

    # Check if there's a stored image for this user
    temp_image_path = msg_response.get_temp_image(user_id)
    
    if temp_image_path:
        try:
            # Process the image with the additional information
            response = msg_response.process_image_with_info(temp_image_path, msg)
            
            # Clear the stored image path
            msg_response.clear_temp_image(user_id)

            Preplexity_answer, questions = msg_response.Perplexity_response(f"Provide more information from this object describe:{response}")
            
            # Split the questions and filter out any empty strings
            last_questions = questions.split("\n")

            # Save chat history
            msg_response.save_chat_history(user_id, msg, Preplexity_answer)

            quick_reply_buttons = create_quick_reply_buttons(last_questions)

            messages = [
                TextSendMessage(text=Preplexity_answer),
                TextSendMessage(text=f"以下是後續問題：\n{questions}"),
                TextSendMessage(
                    text="選擇一個問題編號來獲取更多信息：",
                    quick_reply=QuickReply(items=quick_reply_buttons)
                )
            ]
            line_bot_api.reply_message(event.reply_token, messages)
        except Exception as e:
            logger.exception(f"Error processing image with info: {e}")
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage('處理您的請求時發生錯誤，請稍後再試。')
            )
    else:
        if msg.isdigit() and 1 <= int(msg) <= len(last_questions):
            question_index = int(msg) - 1
            logger.debug(last_questions) # Test
            select_question = last_questions[question_index]
            try:
                # Modify the response that LLM don't need to rephrase it.
                Preplexity_answer, new_questions = msg_response.Perplexity_response(select_question, rephrase=False)
                last_questions = new_questions.split('\n')
                msg_response.save_chat_history(user_id, msg, Preplexity_answer)
                quick_reply_buttons = create_quick_reply_buttons(last_questions)

                messages = [
                    TextSendMessage(text=Preplexity_answer),
                    TextSendMessage(text=f"以下是後續問題：\n"),
                    TextSendMessage(
                        text="選擇一個問題編號來獲取更多信息",
                        quick_reply=QuickReply(items=quick_reply_buttons)
                    )
                ]
                logger.debug(f"Reply Message:{messages}")
                line_bot_api.reply_message(event.reply_token, messages)
            except Exception as e:
                logger.exception(traceback.format_exc())
                logger.error(e)
                line_bot_api.reply_message(
                    event.reply_token, 
                    TextSendMessage('處理您的請求時發生錯誤，請稍後再試。')
                )
        elif msg == '0':
            msg_response.clear_memory()
            line_bot_api.reply_message(
                event.reply_token,
                TextMessage("已刪除歷史紀錄")
            )
        else:
            try:
                Preplexity_answer, questions = msg_response.Perplexity_response(msg)
                last_questions = questions.split('\n')
                msg_response.save_chat_history(user_id, msg, Preplexity_answer)
                quick_reply_buttons = create_quick_reply_buttons(last_questions)

                messages = [
                    TextSendMessage(text=Preplexity_answer),
                    TextSendMessage(text=f"以下是後續問題：\n{questions}"),
                    TextSendMessage(
                        text="選擇一個問題編號來獲取更多信息：",
                        quick_reply=QuickReply(items=quick_reply_buttons)
                    )
                ]
                line_bot_api.reply_message(event.reply_token, messages)
            except Exception as e:
                logger.exception(traceback.format_exc())
                logger.error(e)
                line_bot_api.reply_message(
                    event.reply_token, 
                    TextSendMessage('處理您的請求時發生錯誤，請稍後再試。')
                )

# 處理音訊訊息
@handler.add(MessageEvent, message=AudioMessage)
def handle_audio_message(event):
    audio_content = line_bot_api.get_message_content(event.message.id)
    user_id = event.source.user_id
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
        last_questions = questions.split('\n')
        
        # Save chat history
        msg_response.save_chat_history(user_id, msg, Preplexity_answer)

        quick_reply_buttons = create_quick_reply_buttons(last_questions)


        messages = [
            TextSendMessage(text=Preplexity_answer),
            TextSendMessage(text=f"以下是後續問題：\n{questions}"),
            TextSendMessage(
                text="選擇一個問題編號來獲取更多信息",
                quick_reply=QuickReply(items=quick_reply_buttons)
            )
        ]
        line_bot_api.reply_message(event.reply_token, messages)
    except Exception as e:
        logger.exception(f"Error handling audio message:{e}")
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
    message_content = line_bot_api.get_message_content(event.message.id)

    # Save the image to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_image:
        for chunk in message_content.iter_content():
            temp_image.write(chunk)
        temp_image_path = temp_image.name

    # Store the temporary file path in the user's session
    user_id = event.source.user_id
    msg_response.store_temp_image(user_id, temp_image_path)

    # Ask the user for more information
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="請提供更多關於這張圖片的信息或問題。")
    )

@handler.add(PostbackEvent)
def handle_message(event):
    print(event.postback.data)


@handler.add(MemberJoinedEvent)
def welcome(event):
    uid = event.joined.members[0].user_id
    gid = event.source.group_id
    profile = line_bot_api.get_group_member_profile(gid, uid)
    name = profile.display_name
    message = TextSendMessage(text=f'{name}歡迎加入, 輸入 0 來清除之前的歷史對話')
    line_bot_api.reply_message(event.reply_token, message)

def send_message_to_api(user_id, user_message, bot_response):
    api_url = "http://216.24.60.0/24:5000/api/messages"  # Use your actual server address in production
    
    payload = {
        "user_id": user_id,
        "user_message": user_message,
        "bot_response": bot_response
    }

    try:
        response = requests.post(api_url, json=payload)
        response.raise_for_status()
        logger.info(f"Successfully sent messages to API for user {user_id}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send messages to API: {e}")

# New API endpoint to receive messages
@app.route("/api/messages", methods=['POST'])
def receive_messages():
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    user_id = data.get('user_id')
    user_message = data.get('user_message')
    bot_response = data.get('bot_response')

    if not all([user_id, user_message, bot_response]):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        # Here you would typically save this data to a database
        # For this example, we'll just log it
        logger.info(f"Received message data: User ID: {user_id}, "
                    f"User Message: {user_message}, Bot Response: {bot_response}")

        # In a real application, you might do something like:
        # save_message_to_database(user_id, user_message, bot_response)

        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.error(f"Error processing message data: {e}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port)
