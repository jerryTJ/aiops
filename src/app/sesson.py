from langchain_mcp_adapters.tools import load_mcp_tools


async def use_stateful_session():
    client = MultiServerMCPClient({
        "database": {
            "transport": "streamable_http",
            "url": "http://127.0.0.1:3000/mcp",
        }
    })

    # Use session to maintain state
    async with client.session("database") as session:
        tools = await load_mcp_tools(session)
        
        agent = create_agent(
            model=ChatOpenAI(model="gpt-4o-mini"),
            tools=tools
        )
        
        result = await agent.ainvoke({"messages": [...]})

