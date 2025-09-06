from flask import Flask, request, Response, stream_with_context, render_template
import os
import json
import uuid
from doc2md import docx_to_markdown
from ollamaDemo import  query_system, create_vector, ollama_query_stream,get_reference
from deepseek import DeepSeekChat
from langchain_core.messages import HumanMessage

app = Flask(__name__)


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
    if not file.filename.endswith((".doc", ".docx", ".pdf")):
        return Response("Invalid file type. Only .doc and .docx are allowed.", 400)

    try:
        temp_filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
        filepath = os.path.join("./", temp_filename)

        file.save(filepath)
        index_name = request.args.get("index_name", "child_english")
        create_vector(filepath, index_name)
        if file.filename.endswith((".pdf")):
            return Response("PDF uploaded successfully", 200)

        return Response(
            stream_with_context(docx_to_markdown(filepath)),
            mimetype="text/event-stream",
        )
    except Exception as e:
        return Response(f"An error occurred: {str(e)}", 500)
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)



@app.route("/api/query", methods=["GET"])
def query():
    prompt = request.args.get("prompt")
    # 使用示例
    api_key = os.getenv("OPENAI_API_KEY","sk-50a69787ac4343dcb9f813c0aafe3b90")
    streaming  = True
    chat = DeepSeekChat(api_key=api_key,streaming=streaming)
    if streaming:
    # 创建流式响应
        def generate_stream():
        # 调用模型的流式接口
            for chunk in chat.stream([HumanMessage(content="你好")]):
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
        response = chat.invoke([HumanMessage(content="你好！")])
        print(response.content)
    ## involved local LLM
    index_name = request.args.get("index_name")
    result = ollama_query_stream(prompt, index_name)
    # Ensure Chinese characters are returned correctly, not as Unicode escapes
    return Response(json.dumps({"result": result}, ensure_ascii=False), mimetype='application/json; charset=utf-8', status=200)


@app.route("/api/chat", methods=["POST"])
def stream():
    data = request.get_json()
    prompt = data.get("prompt", "")
    index_name = data.get("index_name", "child_english")
    # 创建流式响应
    context = get_reference(prompt, index_name),
    return Response(
        ollama_query_stream(context, prompt),
        mimetype="text/event-stream;charset=utf-8'",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用Nginx缓冲
        }, 

        status=200
    )


def run():
    app.run(debug=True, port=5001)


if __name__ == "__main__":
    run()
