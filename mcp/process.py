# process_server.py
from mcp.server.fastmcp import FastMCP
import psutil

mcp = FastMCP("process-server")

@mcp.tool()
def process_info() -> dict:
    """获取系统进程信息"""
    processes = []
    for proc in psutil.process_iter(["pid", "name", "username"]):
        processes.append(proc.info)
    return {"processes": processes}

if __name__ == "__main__":
    mcp.run()   # 使用 stdio 作为通信通道