import subprocess
import json
def run_liquibase(sql_config: str, db_config: str) -> str:
    """
    使用 Liquibase 执行 changeLog 变更文件。
    验证大模型生成回滚语句是否有效
    """
    sql_info = json.loads(sql_config)
    user = sql_info["user"]
    change_id = sql_info["id"]
    attributes = sql_info["attributes"]
    rollback = sql_info["rollback"]
    sql = sql_info["sql"]
    comment = sql_info["comment"]
    change_log_file = create_change_file(sql,rollback, user, change_id, attributes, comment)
    
    db_info = json.loads(db_config)
    url = db_info["url"]
    db_user= db_info["username"]
    db_pwd = db_info["pwd"]
    cmd = [
        "liquibase",
        f"--driver=com.mysql.cj.jdbc.Driver",
        f"--changeLogFile={change_log_file}", 
        f"--url={url}",
        f"--username={db_user}",
        f"--password={db_pwd}",
        f"--searchPath=.",
        f"update"
    ]

    rollback_cmd = [
        "liquibase",
        f"--driver=com.mysql.cj.jdbc.Driver",
        f"--changeLogFile={change_log_file}",
        f"--url={url}",
        f"--username={db_user}",
        f"--password={db_pwd}",
        f"--searchPath=. ",
        f"rollbackCount",
        f"1"
    ]
    print("执行命令:", " ".join(cmd))
    print("执行命令:", " ".join(rollback_cmd))
    result = {}
    try:
        execute_result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        result["execute_result"]= execute_result.stdout
        rollback_result = subprocess.run(rollback_cmd, capture_output=True, text=True, check=True)
        result["rollback_result"]=rollback_result.stdout
    except subprocess.CalledProcessError as e:
        print(e.stderr)
        result["error"] =f"Liquibase 执行失败:{e.stderr}"
    
    return json.dumps(result)

def create_change_file(execute_sql: str, rollback: str, user: str, change_id: str, attributes: list, comment: str):
    file_path = f"chanageSet_{change_id}.sql"
    change_id= user+":"+change_id
    attribute = attributes.join(" ")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(f"--liquibase formatted sql \n--changeset {change_id} {attribute}\n--comment:{comment}\n{execute_sql}\n--rollback {rollback}")
    return file_path


if __name__ == "__main__":
    sql_config='{"sql":"update histories set created_at = now();","user":"jerry","id":"2025-11-24","attributes":"labels:example-label context:example-context","rollback":"update histories set created_at = \'2025-11-24 10:56:16\';","comment":"test mcp"}'

    db_config='{"url":"jdbc:mysql://localhost:3306/applier","username":"root","pwd":"Admin@123"}'

    run_liquibase(sql_config, db_config)