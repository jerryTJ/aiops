
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from pathlib import Path
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from liquibase.tracer.tracer import AgentTracer
from langchain_core.messages import AIMessage


async def check_changesets(change_sets: str, db_config: dict):
    if change_sets is None or len(change_sets) == 0:
        return "请提供检验的change sets"
    # Configure client to connect to your streamable_http server
    client = MultiServerMCPClient({
        "database": {
            "transport": "streamable_http",
            # Replace with your actual server URL and port
            "url": "http://127.0.0.1:3000/mcp",
        }
    })

    # Load tools from your MCP serv
    tools = await client.get_tools()
    # Print available tools
    for tool in tools:
        print(f"Tool: {tool.name}")
        print(f"  Description: {tool.description}")
        print("Tool:", tool.name, " strict=", getattr(tool, "strict", None))

    llm = create_deepseek()
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=load_system_prompt(file_path="prompt/check_changeset_prompt.md")
        
    )
    if db_config is None:
        db_config = {
            "db_url": "localhost:3306",
            "db_name":"applier",
            "username": "root",
            "pwd": "Admin@123"
        }
   
    db_config = json.dumps(db_config)
    tracer = AgentTracer(log_file="logs/trace_log.json")
    query_content = f"以下changeSet {change_sets},进行检验, db_config :{db_config}"
    response = await agent.ainvoke(
        {
        "messages": [{
            "role": "user",
            "content": query_content
        }],
        },
        config={"callbacks": [tracer]} 
    )
    return extract_final_answer(response)


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


def create_deepseek():
    deepseek_api_key = "sk-ef97829f953a4b09bc800885d55e0ee1"  # 替换为你的 DeepSeek API Key
    base_url = "https://api.deepseek.com"
    # Create agent with your MCP tools
    # 初始化 DeepSeek 模型
    llm = ChatOpenAI(
        # model="deepseek-chat",  # DeepSeek 模型
        model="deepseek-reasoner",  # DeepSeek 模型
        temperature=0,
        openai_api_key=deepseek_api_key,
        openai_api_base=base_url,  # DeepSeek API 地址
        model_kwargs={
            "top_p": 0.95,
        }
    )
    return llm


def extract_final_answer(resp):
    results = []
    messages = resp["messages"]
    for message in messages:
        if isinstance(message, AIMessage):
            results.append(message.content)
    return "\n".join(results)

