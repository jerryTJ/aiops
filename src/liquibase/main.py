from flask import Flask, request, Response, render_template, session, send_from_directory
from liquibase.agent.create_changeset import ask_llm
import re
import os
import uuid
import asyncio
import json
from datetime import datetime

app = Flask(__name__)

app.secret_key = "50a69787ac4343ew3cb9f813c0aafe3b90"


@app.route("/")
def index():
    return render_template("index.html")


def sse_format(message: str) -> str:
    """格式化为 SSE 输出格式"""
    return f"{message}\n"


def sse_event(event, data):
    """
    生成一条标准 SSE 事件
    """
    return f"event: {event}\ndata: {data}\n\n"


@app.route("/api/upload", methods=["POST"])
def create_changeset():
    if "file" not in request.files:
        return Response("No file part", status=400)
    file = request.files["file"]
    if file.filename == "":
        return Response("No file part", status=400)
    if not file.filename.endswith((".sql")):
        return Response("Invalid file type. Only sql are allowed.", 400)

    try:
        temp_filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
        filepath = os.path.join("/tmp/", temp_filename)

        file.save(filepath)
        cache_db_info(file_path=filepath, forms=request.form)
        dev_db_config = session["dev_db_config"]
        prod_db_config = session["prod_db_config"]
        db_name = session["db_name"]
        change_sets = []

        def generate():
            sql_list = parse_sql_file(filepath)
            if not sql_list:
                yield sse_event("message", "No SQL found.")
                return

            for idx, sql in enumerate(sql_list, 1):
                yield sse_event("message", f"[正在解析第{idx}条sql:]{sql}")
                
                # LLM 调用
                result = asyncio.run(ask_llm(sql, dev_db_config, prod_db_config, db_name))
                if result["status"] == "success":
                    yield sse_event("message", "生成的ChangeSet如下:")
                    change_sets.append({"index": idx, "sql": sql, "result":result["message"]})
                    # 按行输出
                    for line in result["message"].split("\n"):
                        yield sse_event("message", f"{line}")
                else:
                    yield sse_event("message", f"解析第{idx}条sql生成ChangeSet失败，原因如下:")
                    yield sse_event("message", result["message"])
                    yield sse_event("message", "如果进行修改，请重新输入修改后的sql")
            # 所有sql处理完后，写入changeSet文件
            file_name = write_list_split_by_newline(change_sets, db_name, mode="w", encoding="utf-8")
            yield sse_event("message", "changeSet文件已生成，可以点击右上角的链接下载")
            url = f"http://127.0.0.1:5001/download/{file_name}"
            yield sse_event("control", json.dumps({"url": url}))
            yield sse_event("done", "end") 

        return Response(
                generate(),
                mimetype="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Accel-Buffering": "no"
                }
        )
        
    except Exception as e:
        return Response(f"An error occurred: {str(e)}", 500)


def cache_db_info(file_path: str, forms: dict):
    dialect = forms["dialect"]
    db_addr = forms["db_addr"].rsplit("/", 1)
    db_url = db_addr[0]
    db_name = db_addr[1]
    db_user = forms["db_user"]
    db_pwd = forms["db_pwd"]
    prod_db_addr = forms["prod_db_addr"].rsplit("/", 1)
    prod_db_url = prod_db_addr[0]
    prod_db_name = prod_db_addr[1]
    prod_db_user = forms["prod_db_user"]
    prod_db_pwd = forms["prod_db_pwd"]
    dev_db_config = {
        "db_url": db_url,
        "db_name": db_name,
        "username": db_user,
        "pwd": db_pwd,
        "dialect": dialect
    }
    prod_db_config = {
        "db_url": prod_db_url,
        "db_name": prod_db_name,
        "username": prod_db_user,
        "pwd": prod_db_pwd,
        "dialect": dialect
    }
    session["sql_file"] = file_path
    session["db_name"] = db_name
    session["dev_db_config"] = dev_db_config
    session["dev_db_pwd"] = db_pwd
    session["prod_db_config"] = prod_db_config


def parse_sql_file(path: str) -> list[str]:
    """
    读取 SQL 文件，以 ; 结尾拆分 SQL 语句
    支持处理 \\n、空格、注释等
    """
    with open(path, encoding="utf-8") as f:
        content = f.read()

    # 去掉注释（-- 注释）
    content = re.sub(r'--.*', '', content)

    # 按 ; 拆分，并 strip 过滤空字符串
    sql_list = [stmt.strip() for stmt in content.split(";") if stmt.strip()]
    return sql_list


def write_list_split_by_newline(data_list, db_name, mode="w", encoding="utf-8"):
    now_str = datetime.now().strftime("%Y_%m_%d")
    file_name = f"changeSet_{db_name}_{now_str}.sql"
    file_path = f"/tmp/{file_name}"
    with open(file_path, mode, encoding=encoding) as f:
        f.write("--liquibase formatted sql\n")
        for item in data_list:
            idx = item["index"]
            result = item["result"]
            f.write("\n")
            f.write(f"/* [第{[idx]}条] */\n")
            for line in str(result).splitlines():
                f.write(line + "\n")
    return file_name


BASE_DIR = "/tmp"


@app.route("/download/<path:filename>")
def download(filename):
    return send_from_directory(
        BASE_DIR,
        filename,
        as_attachment=True
    )


@app.route("/api/chat", methods=["POST"])
def repaire_sql():
    data = request.get_json()
    prompt_sql = data.get("prompt", "")
    if prompt_sql == "":
        return Response(sse_event("message", "请输入sql"), mimetype="text/event-stream")
    dev_db_config = session["dev_db_config"]
    prod_db_config = session["prod_db_config"]
    db_name = session["db_name"]
    if dev_db_config is None or dev_db_config == "":
        return Response(sse_event("message", "请先上传sql文件和配置数据库信息"), mimetype="text/event-stream")

    def generate():
        # LLM 调用
        result = asyncio.run(ask_llm(prompt_sql, dev_db_config, prod_db_config, db_name))
        if result["status"] == "success":
            yield sse_event("message", "生成的ChangeSet如下:")
            # 按行输出
            for line in result["message"].split("\n"):
                yield sse_event("message", f"{line}")
        else:
            yield sse_event("message", "生成ChangeSet失败，原因如下:")
            # 按行输出
            for line in result["message"].split("\n"):
                yield sse_event("message", f"{line}")
            yield sse_event("message", "如果进行修改，请重新输入修改sql")

    return Response(generate(), mimetype="text/event-stream")


def run():
    app.run(debug=True, port=5001)


if __name__ == "__main__":
    run()
