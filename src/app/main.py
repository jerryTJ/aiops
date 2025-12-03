from flask import Flask, request, Response, render_template, session
from urllib.parse import quote, quote_plus
import os
import json
import uuid
from deepseek import DeepSeekChat
from langchain_core.messages import HumanMessage

app = Flask(__name__)

app.secret_key = "50a69787ac4343ew3cb9f813c0aafe3b90"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/upload", methods=["POST"])
def upload_file():
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
        return Response("上传文件成功，等待解析" , 200)

    except Exception as e:
        return Response(f"An error occurred: {str(e)}", 500)


def cache_db_info(file_path: str, forms: dict):
    dialect = forms["dialect"]
    db_addr = forms["db_addr"]
    db_user = forms["db_user"] 
    db_pwd = forms["db_pwd"]
    prod_db_addr = forms["prod_db_addr"]
    prod_db_user = forms["prod_db_user"]
    prod_db_pwd = forms["prod_db_pwd"]
    if dialect == "mysql":
        prod_db_pwd = quote(prod_db_pwd)
        prod_pymysql_url = f"mysql+pymysql://{prod_db_user}:{prod_db_pwd}@{db_addr}"
        session["prod_pymysql_url"] = prod_pymysql_url

        dev_jdbc_url = f"jdbc:mysql://{db_addr}"
        session["dev_jdbc_url"] = dev_jdbc_url

        prod_jdbc_url = f"jdbc:mysql://{prod_db_addr}"
        session["prod_jdbc_url"] = prod_jdbc_url
    # mysql+pymysql://root:Admin%40123@localhost:3306/applier
    # jdbc:mysql://localhost:3306/applier
    session['sql_file'] = file_path
    session['dev_db_user'] = db_user
    session['dev_db_pwd'] = db_pwd
    session['prod_db_user'] = prod_db_user
    session['prod_db_pwd'] = prod_db_pwd


@app.route("/api/query", methods=["GET"])
def query():
    prompt = request.args.get("prompt")
    # 使用示例
    api_key = os.getenv("OPENAI_API_KEY", "sk-50a69787ac4343dcb9f813c0aafe3b90")
    streaming = True
    chat = DeepSeekChat(api_key=api_key, streaming=streaming)
    result = {}
    if streaming:

    # 创建流式响应
        def generate_stream():
        # 调用模型的流式接口
            for chunk in chat.stream([HumanMessage(content=prompt)]):
                # 转换为 SSE 格式：data: {content}\n\n
                content = chunk.content
                yield f"{json.dumps({'content': content})}\n\n"
            # 添加流结束标记（可选）
            yield "[DONE]\n\n"

        return Response(
            generate_stream(),
            mimetype="text/event-stream;charset=utf-8'",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # 禁用Nginx缓冲
            },

            status=200
        )

    else:
        response = chat.invoke([HumanMessage(content=prompt)])
        result = response.content
    return Response(json.dumps({"result": result}, ensure_ascii=False), mimetype='application/json; charset=utf-8', status=200)


def run():
    app.run(debug=True, port=5001)


if __name__ == "__main__":
    run()
