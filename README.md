# xx_to_markdown

## cr.weaviate.io/semitechnologies/weaviate:1.29.1

## init env

pip install -r requirements.txt --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host=files.pythonhosted.org

## install ollam

 <https://ollama.com/download>

## install  deepseek model

  ollama pull deepseek-r1:7b
  ollama run deepseek-r1:7b

## install vector model (embedding)

ollama pull snowflake-arctic-embed:335m

## start weaviate /Users/jerry/LLM/weaviate

docker-compose -f docker-compose.yaml up -d

### install poetry

  pip install poetry --trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host pypi.python.org transformers --user --disable-pip-version-check
  poetry self update
  poetry cache clear --all pypi
  poetry update

## curl 调用接口测试

 curl -X POST -F "file=@demo.docx" <http://127.0.0.1:5001/upload>
 curl -X POST <http://127.0.0.1:5001/api/chat>   -H "Content-Type: application/json"  -d '{"prompt": "bluebird", "index_name": "child_english"}'

## --no-buffer  

curl -X POST <http://127.0.0.1:5001/api/chat>   -H "Content-Type: application/json"  --no-buffer  -d '{"prompt": "bluebird", "index_name": "child_english"}'

curl -X GET <http://localhost:5001/api/query?prompt=你好> -H "Content-Type: application/json"  --no-buffer

# 本地测试安装

pip install dist/my_package-0.1.0-py3-none-any.whl
pip uninstall dist/xx_to_markdown-0.1.0-py3-none-any.whl

# 验证命令行工具

mycli --help

# delete weaviate collection

curl -X DELETE  <http://localhost:8080/v1/schema/Child_english>   -H 'Content-Type: application/json'

# 验证删除结果

curl <http://localhost:8080/v1/schema> | jq .classes[].class

# pyenv-安装python版本

python global 3.10.16
python local 3.10.16
python   versions
pyenv  install/uninstall  3.10.16

pip show flask

# 创建单独的应用环境

python -m venv ./env-name

sourece .python-env/bin/activate

# set python interpreter

在 VS Code 中选择正确的 Python 解释器

 1. 打开 VS Code。
 2. 按 Cmd+Shift+P（Mac）或 Ctrl+Shift+P（Windows/Linux）打开命令面板。
 3. 输入并选择：Python: Select Interpreter
 4. 选择你安装 Flask 的解释器，比如：

# pip package

langchain-openai 1.1.0
langchain-mcp-adapters 0.1.14
mcp 1.22.0
langchain-mcp 0.2.1
