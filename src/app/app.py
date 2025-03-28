from flask import Flask, request, Response, stream_with_context, render_template, g
import os
import json
import uuid
import asyncio
import sqlite3 # Added SQLite import
from doc2md import docx_to_markdown
from ollamaDemo import query_system, create_vector, query_stream
from deepseek import DeepSeekChat
from langchain_core.messages import HumanMessage

app = Flask(__name__)

# --- Database Setup ---
DATABASE = 'database.db'

def get_db():
    """Opens a new database connection if there is none yet for the current application context."""
    if 'db' not in g:
        g.db = sqlite3.connect(
            DATABASE,
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row # Return rows as dictionary-like objects
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    """Closes the database again at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

# Command to initialize DB (can be run via 'flask init-db')
@app.cli.command('init-db')
def init_db_command():
    """Clear existing data and create new tables."""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        # Drop tables if they exist (for clean setup during development)
        print("Dropping existing tables (if any)...")
        cursor.execute("DROP TABLE IF EXISTS user_responses;")
        cursor.execute("DROP TABLE IF EXISTS scenarios;")
        # Create tables
        print("Creating 'scenarios' table...")
        cursor.execute("""
            CREATE TABLE scenarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                chinese_content TEXT NOT NULL,
                english_content TEXT NOT NULL UNIQUE, -- Ensure uniqueness for lookups
                example_answer TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("Creating 'user_responses' table...")
        cursor.execute("""
            CREATE TABLE user_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT NOT NULL,
                scenario_id INTEGER NOT NULL,
                user_answer TEXT NOT NULL,
                score INTEGER,
                optimized_answer TEXT,
                llm_example_answer TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (scenario_id) REFERENCES scenarios (id)
            );
        """)
        conn.commit()
        print('Initialized the database tables successfully.')
    except sqlite3.Error as e:
        print(f"An error occurred during DB initialization: {e}")
    finally:
        if conn:
            conn.close()


# Initialize DB connection handling and ensure tables exist
def init_app(app):
    """Register database functions with the Flask app and ensure tables exist."""
    app.teardown_appcontext(close_db)
    # Check if tables exist on startup, if not, create them.
    try:
        # Use a separate connection for initialization check to avoid context issues
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='scenarios';")
        if cursor.fetchone() is None:
             print("Database tables not found. Creating them...")
             cursor.execute("""
                CREATE TABLE scenarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    chinese_content TEXT NOT NULL,
                    english_content TEXT NOT NULL UNIQUE,
                    example_answer TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
             cursor.execute("""
                CREATE TABLE user_responses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_name TEXT NOT NULL,
                    scenario_id INTEGER NOT NULL,
                    user_answer TEXT NOT NULL,
                    score INTEGER,
                    optimized_answer TEXT,
                    llm_example_answer TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (scenario_id) REFERENCES scenarios (id)
                );
            """)
             conn.commit()
             print("Created database tables.")
        else:
            print("Database tables already exist.")
        conn.close()
    except sqlite3.Error as e:
        print(f"Database error during init_app check: {e}")
        # Consider raising the error or handling it more robustly

# Initialize DB with app instance
init_app(app)
# --- End Database Setup ---


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
                yield f"{json.dumps({'content': content},ensure_ascii=False)}\n\n"
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
    index_name = request.args.get("index_name")
    result = index_name# query_system(prompt, index_name)
    # Ensure Chinese characters are returned correctly, not as Unicode escapes
    return Response(json.dumps({"result": result}, ensure_ascii=False), mimetype='application/json; charset=utf-8', status=200)


@app.route("/api/chat", methods=["POST"])
def stream():
    data = request.get_json()
    prompt = data.get("prompt", "")
    index_name = data.get("index_name", "child_english")
    # 创建流式响应
    return Response(
        query_stream(prompt, index_name),
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
