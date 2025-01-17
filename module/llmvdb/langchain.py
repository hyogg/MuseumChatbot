import os
import dotenv

from typing import Optional
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langchain.callbacks import get_openai_callback

dotenv.load_dotenv()

class LangChain:
    def __init__(self, api_token=None, instruction=None, callbacks=None, verbose=False):
        self.api_token = api_token or os.getenv("OPENAI_API_KEY") or None
        if self.api_token is None:
            raise ValueError("Open API 키가 필요합니다")
        self.instruction = instruction
        self.callbacks = callbacks
        self.verbose = verbose
        self.streaming = False if self.callbacks is None else True
        self.model = "gpt-3.5-turbo-1106"
        self.llm = ChatOpenAI(
            model=self.model,
            temperature=0.3,
            streaming=self.streaming,
            callbacks=self.callbacks,
        )
        self.system_message = f"{self.instruction}\n 유저의 질문이 들어오면 주어지는 참고용 문서들을 바탕으로 문맥에 맞게 해석해서 답변해줘. \n 만약 해당 문서에서 질문에 대한 답변을 찾을 수 없으면 반드시 '참고할 수 있는 문서가 없습니다.'라고 말해야 해. 그 후에 네가 기존에 아는 정보를 간략히 말해줘."
        self.history_memory = []
        self.initial_history_memory = [SystemMessage(content=self.system_message)]

    def append_limit_length(self, human_message, ai_message):
        new_pair_len = len(human_message.content) + len(ai_message.content)

        while (
            sum(len(msg.content) for msg in self.history_memory) + new_pair_len > 3000
        ):
            self.history_memory.pop(0)
            self.history_memory.pop(0)
        self.history_memory.append(human_message)
        self.history_memory.append(ai_message)

    def call(self, prompt: str, document: str) -> str:
        with get_openai_callback() as cb:
            response = self.llm(
                self.initial_history_memory
                + self.history_memory
                + [
                    HumanMessage(
                        content=f"질문:\n{prompt}\n\n ### 참고용 문서:\n{document}"
                    )
                ]
            )

        if self.verbose:
            print(cb)

        response = response.content
        print(response)

        self.append_limit_length(
            HumanMessage(content=prompt), AIMessage(content=response)
        )
        return response

    def set_callbacks(self, callbacks):
        self.llm = ChatOpenAI(
            model=self.model,
            temperature=0.3,
            streaming=self.streaming,
            callbacks=callbacks,
        )
