# log_server.py
from mcp.server.fastmcp import FastMCP
import os
LOG_DIR = "/var/log"

mcp = FastMCP("log-server")

@mcp.tool()
def list_logs() -> dict:
    """列出 /var/log 下的日志文件"""
    try:
        files = [f for f in os.listdir(LOG_DIR) if os.path.isfile(os.path.join(LOG_DIR, f))]
        return {"log_files": files}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def read_log(filename: str, n: int = 10) -> dict:
    """读取指定日志文件的前 n 行"""
    file_path = os.path.join(LOG_DIR, filename)
    if not os.path.isfile(file_path):
        return {"error": f"File {filename} not found in {LOG_DIR}"}
    
    try:
        lines = []
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for i in range(n):
                line = f.readline()
                if not line:
                    break
                lines.append(line.strip())
        return {"filename": filename, "lines": lines}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    mcp.run()