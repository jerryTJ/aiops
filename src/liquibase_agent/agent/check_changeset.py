from langchain.agents import create_agent

import json
from liquibase_agent.tracer.tracer import AgentTracer
from langchain_core.messages import AIMessage
from liquibase_agent.tools.liquibase import list_tools
from liquibase_agent.agent.baseagent import BaseAgent


class CheckChangesetAgent(BaseAgent):
    deepseek_api_key = (
        "sk-ef97829f953a4b09bc800885d55e0ee1"  # 替换为你的 DeepSeek API Key
    )
    base_url = "https://api.deepseek.com"

    def __init__(self, db_config: str, liquibase_script: str):
        super().__init__(deepseek_api_key=self.deepseek_api_key, base_url=self.base_url)
        self.db_config = db_config
        self.liquibase_script = liquibase_script

    async def check_changesets(self, change_sets: str):
        if change_sets is None or len(change_sets) == 0:
            return "请提供检验的change sets"
        # Load tools from your MCP serv
        tools = await list_tools()

        llm = self.create_deepseek()
        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=super().load_system_prompt(
                file_path="prompt/check_changeset_prompt.md"
            ),
        )

        db_config = json.dumps(self.db_config)
        tracer = AgentTracer(log_file="logs/trace_log.json")
        query_content = f"以下changeSet {change_sets},进行检验, db_config :{db_config}"
        response = await agent.ainvoke(
            {
                "messages": [{"role": "user", "content": query_content}],
            },
            config={"callbacks": [tracer]},
        )
        return self.extract_final_answer(response)

    def extract_final_answer(self, resp):
        results = []
        messages = resp["messages"]
        for message in messages:
            if isinstance(message, AIMessage):
                results.append(message.content)
        return "\n".join(results)
