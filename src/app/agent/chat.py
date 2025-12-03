
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from pathlib import Path
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from app.tracer.tracer import AgentTracer
from langchain_core.messages import AIMessage


def load_system_prompt(file_path: str) -> str:
    """
    从文件中读取 system prompt
    
    Args:
        file_path: system prompt 文件路径
        
    Returns:
        system prompt 内容
    """
    try:
        path = Path(file_path)
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                print(f"Loaded system prompt from: {file_path}")
                return content
        else:
            return get_default_system_prompt()
    except Exception as e:
        print(f"Error loading system prompt: {e}, using default")
        return get_default_system_prompt()


def get_default_system_prompt() -> str:
    """获取默认的 system prompt"""
    return """
      默认提示词
      """


def create_gemini():
    api_key = "AIzaSyBF4Z-RG_5tdWB31SnTpESn6frjHSeOfUI"

    # 初始化 LLM
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",  # 可改：gemini-1.5-pro、gemini-2.0-flash-exp
        google_api_key=api_key,
        temperature=0.2,
    )
    return llm


def create_deepseek():
    deepseek_api_key = "sk-ef97829f953a4b09bc800885d55e0ee1"  # 替换为你的 DeepSeek API Key
    base_url = "https://api.deepseek.com"
    # Create agent with your MCP tools
    # 初始化 DeepSeek 模型
    llm = ChatOpenAI(
        model="deepseek-chat",  # DeepSeek 模型
        temperature=0,
        openai_api_key=deepseek_api_key,
        openai_api_base=base_url,  # DeepSeek API 地址
        model_kwargs={
            "top_p": 0.95,
        }
    )
    return llm


def extract_final_answer(resp):

    messages = resp["messages"]
    message = messages[-1]
    if isinstance(message, AIMessage):
        return extract_sql_content(message.content)
    return dict(message)


def extract_sql_content(text):
    """从文本中提取 ```sql 和 ``` 之间的内容"""
    # 尝试多种可能的标记格式
    markers = ["```sql\n", "```sql\n", "```sql"]
    
    for marker in markers:
        if marker in text:
            start_index = text.find(marker)
            if start_index != -1:
                start_index += len(marker)
                # 查找最近的结束标记
                end_index = text.find("```", start_index)
                if end_index != -1:
                    return text[start_index:end_index].strip()
    return None


async def main():
    # Configure client to connect to your streamable_http server
    client = MultiServerMCPClient({
        "database": {
            "transport": "streamable_http",
            # Replace with your actual server URL and port
            "url": "http://127.0.0.1:3000/mcp",
        }
    })

    # Load tools from your MCP server
    tools = await client.get_tools()
    # Print available tools
    for tool in tools:
        print(f"Tool: {tool.name}")
        print(f"  Description: {tool.description}")
        print("Tool:", tool.name, " strict=", getattr(tool, "strict", None))

    llm = create_deepseek()
    # llm = create_gemini()
   
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=load_system_prompt(file_path="system_prompt.md")
        
    )

    db_config = json.dumps({
        "db_url": "localhost:3306",
        "db_name":"applier",
        "username": "root",
        "pwd": "Admin@123"
    })
    prod_db_config = json.dumps({
        "db_url": "localhost:3306",
        "db_name": "applier",
        "username": "readonly_user",
        "pwd": "readonly@123"})
    # Use agent to validate a liquibase changeset
    tracer = AgentTracer(log_file="trace_log.json")
    response = await agent.ainvoke(
        {
        "messages": [{
            "role": "user",
            "content": f"请对sql update t_users SET name='tom' , nick_name='tom-1' where id = 1 ,生成liquibase changeSet, db_config :{db_config}, prod_db_config:{prod_db_config}, db_name 为applier， 在prod环境执行，作者是jerry"
        }],
        },
        config={"callbacks": [tracer]} 
    )
    return response


if __name__ == "__main__":
    asyncio.run(main())
