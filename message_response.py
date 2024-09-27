from langchain_community.chat_models import ChatPerplexity
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.prompts import ChatPromptTemplate
from openai import OpenAI
import os
import base64
import logging
import openai
import requests

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Message_Response:

    def __init__(self) -> None:
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.Preplexity_API_KEY = os.getenv('PREPLEXITY_API_KEY')
        openai.api_key = self.openai_api_key
        self.temp_images = {}
        self.memory = ConversationBufferWindowMemory(k=5)
        self.setup_chat_models()

    def setup_chat_models(self):
        """setup the model and prompt"""
        self.chat = ChatPerplexity(
            temperature=0.2,
            model="llama-3.1-sonar-small-128k-online",
            pplx_api_key=self.Preplexity_API_KEY,
            max_tokens=2048,
        )

        self.prompt = ChatPromptTemplate.from_template("""
        You are a helpful assistant. Please respond in traditional Chinese (繁體中文).

        {history}

        User: {input}
        Assistant:
        """)

        self.conversation_with_summary = ConversationChain(
            llm=self.chat,
            prompt=self.prompt,
            memory=self.memory,
            verbose=True,
        )

        self.rephrase_llm = ChatOpenAI(
            openai_api_key=self.openai_api_key,
            model_name="gpt-4o-mini",
            temperature=0.8,
            max_tokens=2048,
        )

        self.rephrase_prompt = ChatPromptTemplate.from_template("""
        根據以下對話歷史和用戶訊息，請重新表述用戶的問題，使其更清晰易懂。

        對話歷史：
        {history}

        用戶訊息：{input}

        重新表述後的用戶訊息：
        """)

        self.rephrase_conversation = ConversationChain(
            llm=self.rephrase_llm,
            prompt=self.rephrase_prompt,
            memory=self.memory,
            verbose=False,
        )

        self.further_prompt = ChatPromptTemplate.from_template("""
        根據以下對話歷史和用戶訊息，請提供10個問題給用戶參考提問給 LLM ，讓用戶能知道還能問哪些問題。

        對話歷史：
        {history}

        用戶訊息：{input}

        推薦的問題：
        """)

        self.further_conversation = ConversationChain(
            llm=self.rephrase_llm,
            prompt=self.further_prompt,
            memory=self.memory,
            verbose=False,
        )

    def Perplexity_response(self, text) -> str:
        """Perplexity response."""
        try:
            history = self.get_conversation_history(self.conversation_with_summary.memory)
            rephrased_text = self.rephrase_user_input(text, history)
            response = self.conversation_with_summary.invoke({"input": rephrased_text})
            logger.info(f"Response: {response}")
            further_questions = self.further_question(text, history)
            return response['response'], further_questions
        except Exception as e:
            logger.error(f"Error running the chain: {e}")
            return None, None

    def get_conversation_history(self, memory) -> str:
        """
        從 ConversationBufferWindowMemory 中提取對話歷史，並格式化為文本。
        
        :param memory: ConversationBufferWindowMemory 物件
        :return: 格式化後的對話歷史字符串
        """
        memory_vars = memory.load_memory_variables({})
        return memory_vars.get('history', '')
    
    def rephrase_user_input(self, text, history) -> str:
        """Rephrase user message based on previous message so that LLM can better understand."""
        try:
            rephrase_response = self.rephrase_conversation.invoke({
                "history": history,
                "input": text
            })
            return rephrase_response['response']
        except Exception as e:
            logging.error(f"重新表述時出錯: {e}")
            return text  # 如果重新表述失敗，回傳原始輸入
    
    def further_question(self, text, history) -> str:
        """Provide user further questions to ask."""
        try:
            further_questions_response = self.further_conversation.invoke({
                "history": history,
                "input": text
            })
            return further_questions_response['response']
        except Exception as e:
            logger.error(f"Error: {e}")
            return text

    def transcribe_audio(self, file_path) -> str:
        """Transcribe Audio message to text for LLM."""
        logger.info(f"Starting transcription for file: {file_path}")
        client = OpenAI()
        if not os.path.exists(file_path):
            error_msg = f"Error: The file {file_path} does not exist."
            logger.error(error_msg)
            return error_msg

        try:
            with open(file_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(file=audio_file, model="whisper-1")
            logger.info("Transcription successful.")
            return transcript.text
        except Exception as e:
            error_msg = f"Unexpected error during transcription: {str(e)}"
            logger.error(error_msg)
            return f"轉錄時發生意外錯誤：{str(e)}"

    def get_temp_image(self, user_id):
        """Get the temporary image path for a user."""
        return self.temp_images.get(user_id)

    def store_temp_image(self, user_id, image_path):
        """Store the temporary image path for a user."""
        self.temp_images[user_id] = image_path

    def clear_temp_image(self, user_id):
        """Clear the temporary image path for a user."""
        if user_id in self.temp_images:
            del self.temp_images[user_id]

    def process_image_with_info(self, image_path, additional_info):
        """Process the image with additional information using ChatGPT API."""
        with open(image_path, "rb") as image_file:
            image_base64 = base64.b64encode(image_file.read()).decode('utf-8')

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.openai_api_key}"
        }

        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Here's an image along with additional information: {additional_info}. Please analyze the image considering this information and provide insights."
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
            "max_tokens": 1000
        }

        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        return response.json()['choices'][0]['message']['content']
    
    def clear_memory(self) -> None:
        """Clear all memory"""
        self.memory.clear()