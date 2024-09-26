from langchain_community.chat_models import ChatPerplexity
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.prompts import ChatPromptTemplate
import os
import logging
import openai

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Message_Response:

    def __init__(self) -> None:
        self.openai.api_key = os.getenv('OPENAI_API_KEY')
        self.Preplexity_API_KEY = os.getenv('PREPLEXITY_API_KEY')
        pass

    def Perplexity_response(self, text):
        """Perplexity response."""
        chat = ChatPerplexity(
            temperature=0.2,
            model="llama-3.1-sonar-small-128k-online",
            pplx_api_key=self.Preplexity_API_KEY,
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
        try:
            history = self.get_conversation_history(conversation_with_summary.memory)
            rephrased_text = self.rephrase_user_input(text, history)
            response = conversation_with_summary.invoke({"input": rephrased_text})
            logger.info(f"Response: {response}")
            further_questions = self.further_question(text, history)
            return response['response'], further_questions
        except Exception as e:
            logger.error(f"Error running the chain: {e}")
            return None, None

    def get_conversation_history(self, memory):
        """
        從 ConversationBufferWindowMemory 中提取對話歷史，並格式化為文本。
        
        :param memory: ConversationBufferWindowMemory 物件
        :return: 格式化後的對話歷史字符串
        """
        # 使用 load_memory_variables 來獲取 'history'
        memory_vars = memory.load_memory_variables({})
        return memory_vars.get('history', '')
    
    def rephrase_user_input(self, text, history):
        """Rephrase user message based on previous message so that LLM can better understand."""

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
    
    def further_question(self, text, history):
        """Provide user further questions to ask."""

        rephrase_llm = ChatOpenAI(
            openai_api_key=openai.api_key,
            model_name="gpt-4o-mini",
            temperature=0.8,
            max_tokens=2048,
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