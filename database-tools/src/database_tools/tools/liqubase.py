from sqlalchemy import create_engine, text
from dataclasses import dataclass
import json
import re
import subprocess
from datetime import datetime
from urllib.parse import quote
from sqlalchemy.exc import SQLAlchemyError, OperationalError, ProgrammingError

CHANGESET_ID = {}


class LiquibaseUtils:

    def __init__(self, db_config: str, liquibase_script: str):
        self.db_config = db_config
        self.liquibase_script = liquibase_script

    def execute_liquibase(self) -> str:
        """
        使用 Liquibase 执行 changeLog 变更文件。
        验证大模型生成回滚语句是否有效
        """

        db_info = json.loads(self.db_config)
        url = db_info["db_url"]
        db_name = db_info["db_name"]
        db_user = db_info["username"]
        db_pwd = db_info["pwd"]
        db_url = f"jdbc:mysql://{url}/{db_name}"
        change_log_file = self.create_change_file(db_name, self.liquibase_script)
        cmd = [
            "liquibase",
            f"--driver=com.mysql.cj.jdbc.Driver",
            f"--changeLogFile={change_log_file}",
            f"--url={db_url}",
            f"--username={db_user}",
            f"--password={db_pwd}",
            f"--searchPath=.",
            f"update"
        ]

        rollback_cmd = [
            "liquibase",
            f"--driver=com.mysql.cj.jdbc.Driver",
            f"--changeLogFile={change_log_file}",
            f"--url={db_url}",
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
            liquibase_output = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(liquibase_output.stdout)
            print(liquibase_output.stderr)
            if liquibase_output.returncode == 0:
                change_count = self._get_change_count(liquibase_output.stdout)
                if change_count["total_change_sets"] >= 1:
                    result["status"] = "success"
                    result["message"] = liquibase_output.stdout
                else:
                    result["status"] = "error"
                    result["message"] = liquibase_output.stderr
            else:
                result["status"] = "error"
                result["message"] = liquibase_output.stderr
                
            rollback_result = subprocess.run(rollback_cmd, capture_output=True, text=True, check=True)
            print(rollback_result.stdout)
            print(rollback_result.stderr)
            if rollback_result.returncode == 0:
                result["status"] = "success"
                result["message"] = liquibase_output.stdout
            else:
                result["status"] = "error"
                result["message"] = f"{result['message']}{liquibase_output.stderr}"
        except subprocess.CalledProcessError as e:
            print(e.stderr)
            print(e.stdout)
            result["status"] = "error"
            result["message"] = f"{e.stderr}"

        return result

    def _get_change_count(self, liquibase_output):
        # 使用正则表达式提取Total change sets信息
        pattern = r"Total change sets:\s*(\d+)"
        match = re.search(pattern, liquibase_output)

        result_dict = {"total_change_sets":0}
        if match:
            result_dict["total_change_sets"] = int(match.group(1))

        return result_dict

    def create_change_file(self, db_name: str, liquibase_script:str):
        now_str = datetime.now().strftime("%Y_%m_%d")
        file_path = f"chanageSet_{db_name}_{now_str}.sql"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("--liquibase formatted sql\n")
            f.write("\n")
            f.write(liquibase_script)
        return file_path
    
    def check_changeset(self) -> str:
        """
        使用 Liquibase 执行 changeLog 变更文件。
        验证大模型生成回滚语句是否有效
        """
        db_info = json.loads(self.db_config)
        url = db_info["db_url"]
        db_name = db_info["db_name"]
        db_user = db_info["username"]
        db_pwd = db_info["pwd"]
        db_url = f"jdbc:mysql://{url}/{db_name}"
        change_log_file = self.create_change_file(db_name, self.liquibase_script)
        cmd = [
            "liquibase",
            f"--driver=com.mysql.cj.jdbc.Driver",
            f"--changeLogFile={change_log_file}",
            f"--url={db_url}",
            f"--username={db_user}",
            f"--password={db_pwd}",
            f"--searchPath=.",
            f"updateSQL"
        ]

        print("执行命令:", " ".join(cmd))
        result = {}
        try:
            liquibase_output = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(liquibase_output.stdout)
            print(liquibase_output.stderr)
            result["status"] = "success"
            result["message"] = liquibase_output.stdout
            
        except subprocess.CalledProcessError as e:
            print(e.stderr)
            print(e.stdout)
            result["status"] = "error"
            result["message"] = f"{e.stderr}"
        return result

    @staticmethod
    def create_liquibase_change_id(db_name: str):
        """
        生成Liquibase 的changeSet的ID
        根据应用名称进行递增
        """
        change_id = CHANGESET_ID.get(db_name, 1)
        change_id = change_id + 1
        CHANGESET_ID[db_name] = change_id
        return {"status":"success", "change_id": change_id}

    
@dataclass
class DatabaseUtil:

    def __init__(self, db_config: str):
        self.db_config = db_config

    def query_result_of_prod_by_sql(self, sql: str):
        """
        根据db信息查询变更的sql在生产数据库影响的记录数
        影响的记录大于1条则需要拆分变更的sql
        """
       
        if self.db_config is None:
            return {
                "status": "error",
                "message":"请提供db config",
                "count": 0,
                "data": []
            }
        db_info = json.loads(self.db_config)
        url = db_info["db_url"]
        db_name = db_info["db_name"]
        db_user = db_info["username"]
        db_pwd = quote(db_info["pwd"])

        db_url = f"mysql+pymysql://{db_user}:{db_pwd}@{url}/{db_name}"
        engine = create_engine(db_url)
        if self.if_only_read(engine, "tmp_private_validate"):
            return self.query_update_record(engine, sql)
        return  {
                "status": "error",
                "message":"请提供只读权限的用户",
                "count": 0,
                "data": []
                }

    def query_update_record(self, engine, sql: str):

        with engine.begin() as conn:
            result = conn.execute(text(sql))
            rows = result.mappings().all()

        datas = [dict(row) for row in rows]
        output = {
            "status":"success",
            "count": len(datas),
            "data": datas
        }

        return output

    def if_only_read(self, engine, table_name: str) -> bool:
        """

        判断当前连接用户是否对指定表有 DELETE 权限。
        通过执行 DELETE FROM table WHERE 1=0 来验证权限，
        不会删除任何实际数据。
        """
        try:
            with engine.begin() as conn:
                conn.execute(text(f"CREATE TEMPORARY TABLE {table_name} (id INT)"))
                conn.execute(text(f"INSERT INTO {table_name} (id) VALUES (1)"))
                conn.execute(text(f"UPDATE {table_name} SET id=2 WHERE id=1"))
                conn.execute(text(f"DELETE FROM {table_name} WHERE id=2"))
            return False

        except (OperationalError, ProgrammingError, SQLAlchemyError) as e:
            msg = str(e).lower()

            # 常见权限相关错误关键字
            if any(keyword in msg for keyword in [
                "permission denied",
                "denied",
                "not allowed",
                "privilege",
                "read-only",
                "insufficient"
            ]):
                return True
            # 其它错误直接当无权限处理（也可选择继续抛出）
            return False


if __name__ == "__main__":
    prod_db_config = {
        "db_url": "localhost:3306",
        "db_name": "food",
        "username": "readonly_user",
        "pwd": "readonly@123",
        "dialect": "mysql"
    }
    db_tools = DatabaseUtil(json.dumps(prod_db_config))
    print(db_tools.query_result_of_prod_by_sql("select * from food where vendor='ww' "))
