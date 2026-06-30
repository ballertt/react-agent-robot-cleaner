#提供模型
from abc import ABC, abstractmethod
from typing import Optional
from langchain_core.embeddings import Embeddings
from langchain_community.chat_models.tongyi import BaseChatModel
from langchain_community.embeddings import  DashScopeEmbeddings
from langchain_community.chat_models.tongyi import ChatTongyi
from utils.config_handler import rag_conf

#基础的抽象类继承ABC
class BaseModelFactory(ABC):
    #定义抽象方法,生成器返回嵌入模型和聊天模型
    @abstractmethod
    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        pass

#现在构建子类实现
#ChatModelFactory继承了上面工厂类BaseModelFactory
class ChatModelFactory(BaseModelFactory):
    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        return ChatTongyi(model=rag_conf["chat_model_name"])

class EmbeddingsFactory(BaseModelFactory):
    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        return DashScopeEmbeddings(model=rag_conf["embedding_model_name"])

#获得实例,获得具体模型
chat_model = ChatModelFactory().generator()
embed_model = EmbeddingsFactory().generator()
