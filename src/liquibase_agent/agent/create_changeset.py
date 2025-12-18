import asyncio
from langchain.agents import create_agent
import json
from liquibase_agent.tracer.tracer import AgentTracer
from langchain_core.messages import AIMessage
from liquibase_agent.agent.baseagent import BaseAgent

from liquibase_agent.tools.liquibase import list_tools
from liquibase_agent import agent


class CreateChangesetAgent(BaseAgent):
    deepseek_api_key = (
        "sk-ef97829f953a4b09bc800885d55e0ee1"  # 替换为你的 DeepSeek API Key
    )
    base_url = "https://api.deepseek.com"
    dev_db_config = {
        "db_url": "localhost:3306",
        "db_name": "applier",
        "username": "root",
        "pwd": "Admin@123",
    }
    prod_db_config = {
        "db_url": "localhost:3306",
        "db_name": "applier",
        "username": "readonly_user",
        "pwd": "readonly@123",
    }
    db_name = "default_db"
    author = ("admin",)
    env = "prod"

    def __init__(self, dev_db_config, prod_db_config, db_name, author, env):
        super().__init__(deepseek_api_key=self.deepseek_api_key, base_url=self.base_url)
        self.dev_db_config = dev_db_config or self.dev_db_config
        self.prod_db_config = prod_db_config or self.prod_db_config
        self.db_name = db_name or self.db_name
        self.author = author or self.author
        self.env = env or self.env

    async def question(self, sql: str):
        if sql is None or sql == "":
            return "请提供sql"
        # Load tools from your MCP service
        tools = await list_tools()

        llm = super().create_deepseek()
        # llm = create_gemini()

        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=super().load_system_prompt(
                file_path="prompt/create_changeset_prompt.md"
            ),
        )

        # Use agent to validate a liquibase changeset
        prod_db_config = json.dumps(self.prod_db_config)
        dev_db_config = json.dumps(self.dev_db_config)
        tracer = AgentTracer(log_file="logs/trace_log.json")
        query_content = f"请对sql {sql},生成liquibase changeSet, db_config :{dev_db_config}, prod_db_config:{prod_db_config}, db_name 为{self.db_name}, 在{self.env}境执行，作者:{self.author}"
        response = await agent.ainvoke(
            {
                "messages": [{"role": "user", "content": query_content}],
            },
            config={"callbacks": [tracer]},
        )
        return self.extract_final_answer(response)

    def extract_final_answer(self, resp):

        messages = resp["messages"]
        message = messages[-1]
        if isinstance(message, AIMessage):

            content = self.extract_sql_content(message.content)
            if content is None:
                return {"status": "error", "message": message.content}
            else:
                return {"status": "success", "message": content}
        return {"status": "error", "message": message.content}

    def extract_sql_content(self, text):
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


if __name__ == "__main__":
    agent = CreateChangesetAgent()
    asyncio.run(agent.question("SELECT * FROM users"))
