# client.py
import asyncio
import os
import yaml
from mcp.client.stdio import stdio_client
from mcp.client.session import ClientSession

async def connect_server(name: str, command: list[str]):
    print(f"🔌 Starting {name} -> {command}")
    # 启动 server 子进程并通过 stdio 通信
    async with stdio_client(command) as (read, write):
        session = ClientSession(read, write)
        await session.initialize()

        # 获取工具列表
        tools = await session.list_tools()
        print(f"{name} tools: {tools}")

        # 调用工具
        if name == "process-server":
            result = await session.call_tool("process_info", {})
            print(f"{name} result: {result}")
        elif name == "log-server":
            result = await session.call_tool("list_logs", {})
            print(f"{name} result: {result}")
            # 读取 syslog 前 5 行
            result = await session.call_tool("read_log", {"filename": "syslog", "n": 5})
            print(f"{name} syslog preview: {result}")


async def main():
    current_file_path = os.path.abspath(__file__)
    print(f"当前文件路径: {current_file_path}")
    # 加载配置
    with open("/Users/jerry/workspace/cline/markdown/xx_to_markdown/src/proxy/config.yaml", "r") as f:
        config = yaml.safe_load(f)

    tasks = []
    for server in config["servers"]:
        tasks.append(connect_server(server["name"], server["command"]))

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())