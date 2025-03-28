# xx_to_markdown

## init env

pip install -r requirements.txt

## install ollam

 <https://ollama.com/download>

## install  deepseek model

  ollama pull deepseek-r1:7b
  ollama run deepseek-r1:7b

## install vector model (embedding)

ollama pull snowflake-arctic-embed:335m

## start weaviate

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

curl -X GET  "<http://localhost:5001/api/query?prompt=%22Travel%20Conditions%22&index_name=visa_demo>"  -H "Content-Type: application/json"  --no-buffer

# 本地测试安装

pip install dist/my_package-0.1.0-py3-none-any.whl
pip uninstall dist/xx_to_markdown-0.1.0-py3-none-any.whl

# 验证命令行工具

mycli --help

# delete weaviate collection

curl -X DELETE  <http://localhost:8080/v1/schema/Child_english>   -H 'Content-Type: application/json'

# 验证删除结果

curl <http://localhost:8080/v1/schema> | jq .classes[].class
