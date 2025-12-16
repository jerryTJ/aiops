import json
import weaviate
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_weaviate.vectorstores import WeaviateVectorStore
from langchain.embeddings import OllamaEmbeddings
import ollama

# 配置参数
WEAVIATE_URL = "http://localhost:8080"
OLLAMA_MODEL = "deepseek-r1:7b"  # 选择你安装的模型


# 初始化组件
def initialize_components():
    # 初始化文本分割器
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    # 初始化嵌入模型
    embeddings = OllamaEmbeddings(model="snowflake-arctic-embed:335m")

    # 连接 Weaviate
    client = weaviate.connect_to_local()
    if not client.is_ready():
        raise Exception("Weaviate 服务未启动！")
    return text_splitter, embeddings, client


# 处理 PDF 文件
def process_pdf(file_path, text_splitter, embeddings, client, collection_name):
    collection_name = collection_name.upper()
    # 加载 PDF
    loader = PyPDFLoader(file_path)
    pages = loader.load()

    # 分割文本
    chunks = text_splitter.split_documents(pages)

    # Create vector store using v4 client
    vector_store = WeaviateVectorStore.from_documents(
        documents=chunks,
        embedding=embeddings,
        client=client,
        index_name=collection_name,
    )

    return vector_store


def create_vector(file_path: str, collection_name: str) -> any:
    collection_name = collection_name.upper()
    text_splitter, embeddings, client = initialize_components()

    all_indexs = client.collections.list_all()
    if any(collection_name == k.upper() for k in all_indexs.keys()):
        client.collections.delete(collection_name)

    # 处理 PDF 并创建向量存储
    vector_store = process_pdf(
        file_path, text_splitter, embeddings, client, collection_name
    )
    return vector_store._index_name


# 查询处理
def query_system(question, collection_name):
    collection_name = collection_name.upper()
    embeddings = OllamaEmbeddings(model="snowflake-arctic-embed:335m")

    # 连接 Weaviate
    client = weaviate.connect_to_local()
    if not client.is_ready():
        raise Exception("Weaviate 服务未启动！")
    vector_store = WeaviateVectorStore.from_documents(
        [], embeddings, client=client, index_name=collection_name
    )
    # 向量相似度搜索
    results = vector_store.similarity_search(question, k=3)
    context = "\n\n".join([doc.page_content for doc in results])
    if len(context) <= 0:
        return "未找到相关文档！"

    # 构造 prompt
    prompt = f"""请根据以下上下文回答问题：
    {context}
    
    问题：{question}
    答案："""

    # 使用 Ollama 生成回答
    response = ollama.generate(
        model=OLLAMA_MODEL,
        prompt=prompt,
        stream=False,
        options={"temperature": 0.3, "max_tokens": 1000},
    )

    return response["response"]


def get_reference(question, collection_name)->str:
    collection_name = collection_name.upper()
    embeddings = OllamaEmbeddings(model="snowflake-arctic-embed:335m")

    # 连接 Weaviate
    client = weaviate.connect_to_local()
    if not client.is_ready():
        raise Exception("Weaviate 服务未启动！")
    vector_store = WeaviateVectorStore.from_documents(
        [], embeddings, client=client, index_name=collection_name
    )
    # 向量相似度搜索
    results = vector_store.similarity_search(question, k=3)
    context = "\n\n".join([doc.page_content for doc in results])
    if len(context) <= 0:
        return None

    return context
# 查询处理
def ollama_query_stream(question, context):
    # 构造 prompt
    prompt = f"""请根据以下上下文回答问题：
    {context}
    问题：{question}
    答案："""
    try:
        # 使用 Ollama 生成回答
        response = ollama.generate(
            model=OLLAMA_MODEL,
            prompt=prompt,
            stream=True,
            options={"temperature": 0.3, "max_tokens": 1000},
        )

        for chunk in response:
            # 构造标准化的数据格式
            data = {
                "content": chunk.get("response", ""),
                "DONE": False,
                "error": None,
            }
            yield json.dumps(data,ensure_ascii=False)

        # 结束标记
        yield json.dumps({"DONE": True, "error": None},ensure_ascii=False)


    except Exception as e:
        error_data = {"error": str(e), "DONE": True}
        yield json.dumps(error_data)


# 主程序
def main(question, collection_name):
    answer = query_system(question, collection_name)
    print("\n回答：", answer)


if __name__ == "__main__":
    main("谁是作者？", "child_english")
