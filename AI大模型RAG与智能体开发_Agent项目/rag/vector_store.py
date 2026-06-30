# 向量存储
import os

from langchain_chroma import Chroma
from utils.config_handler import chroma_conf
from model.factory import embed_model
from langchain_text_splitters import RecursiveCharacterTextSplitter
from utils.path_tool import get_abs_path
from utils.file_handler import pdf_loader, txt_loader, listdir_with_allowed_type, get_file_md5_hex
from utils.logger_handler import logger
from langchain_core.documents import Document

class VectorStoreService:
    def __init__(self):
        self.vector_store = Chroma(
            collection_name=chroma_conf['collection_name'],
            embedding_function=embed_model,
            persist_directory=chroma_conf['persist_directory'],
        )                #向量存储实例搞定

        self.spliter = RecursiveCharacterTextSplitter(
            chunk_size=chroma_conf['chunk_size'],
            chunk_overlap=chroma_conf['chunk_overlap'],
            separators=chroma_conf['separators'],
            length_function = len,
        )

    #获取检索器对象
    def get_retriever(self):
        return self.vector_store.as_retriever(search_kwargs={"k": chroma_conf['k']})
    #k:检索的时候，应该返回给我几个匹配的结果

    #加载文档
    def load_document(self):
        """
        从数据文件夹内读取数据文件，转为向量存入向量库
        要计算文件的MD5做去重
        :return:None
        """

        def check_md5_hex(md5_for_check: str):
            if not os.path.exists(get_abs_path(chroma_conf['md5_hex_store'])):
                #创建文件完什么都不写就关闭
                open(get_abs_path(chroma_conf['md5_hex_store']), 'w', encoding="utf-8").close()
                return False               # md5 没处理过

            with open(get_abs_path(chroma_conf['md5_hex_store']), 'r', encoding="utf-8") as f:
                for line in f.readlines():           #把f的所有行读出来
                    line = line.strip()              #把line前后的空格和回车都处理掉
                    if line == md5_for_check:
                        return True        # md5 处理过

                return False                # md5 没处理过

        def save_md5_hex(md5_for_check: str):
            with open(get_abs_path(chroma_conf['md5_hex_store']), 'a', encoding="utf-8") as f:
                #  'a'是追加模式
                f.write(md5_for_check + "\n")

        #加载文档到向量库里面，现在读文件，拿到所有的document对象
        def get_file_documents(read_path: str):
            if read_path.endswith("txt"):
                return txt_loader(read_path)

            if read_path.endswith("pdf"):
                return pdf_loader(read_path)

            return []

        #现在是load_document的主要逻辑

        allowed_files_path: list[str] = listdir_with_allowed_type(
            get_abs_path(chroma_conf['data_path']),
            tuple(chroma_conf["allow_knowledge_file_type"]),
        )

        for path in allowed_files_path:
           # 获取文件的MD5
            md5_hex = get_file_md5_hex(path)

            if check_md5_hex(md5_hex):
               logger.info(f"[加载知识库]{path}内容已经存在知识库中，跳过")
               continue

            try:
                documents: list[Document] = get_file_documents(path)

                if not documents:
                    logger.warning(f"[加载知识库]{path}内没有有效文本内容，跳过")
                    continue

                split_document: list[Document] = self.spliter.split_documents(documents)

                if not split_document:
                    logger.warning(f"[加载知识库]{path}分片后没有有效文本内容,跳过")
                    continue

                #将内容存入向量库
                self.vector_store.add_documents(split_document)

                # 记录这个已经处理好的的文件的md5，避免下次重复加载
                save_md5_hex(md5_hex)

                logger.info(f"[加载知识库]{path}内容加载成功")
            except Exception as e:
                # exc_info为True会记录详细的报错堆栈，如果为False仅记录报错信息本身
                logger.error(f"[加载知识库]{path}加载失败： {str(e)}", exc_info=True)

if __name__ == "__main__":
    vs = VectorStoreService()

    vs.load_document()

    retriever = vs.get_retriever()

    res = retriever.invoke("迷路")
    for r in res:
        print(r.page_content)
        print("-"*20)