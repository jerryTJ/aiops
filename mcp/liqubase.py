"""
Liquibase SQL 验证与测试智能体
集成 Liquibase 和 MCP SQL 服务进行 SQL 验证、执行和回滚测试
"""

import json
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import subprocess
import tempfile
import os


class SQLType(Enum):
    DDL = "DDL"
    DML = "DML"
    INDEX = "INDEX"
    UNKNOWN = "UNKNOWN"


class OperationType(Enum):
    # DDL
    CREATE_TABLE = "CREATE_TABLE"
    ALTER_TABLE = "ALTER_TABLE"
    DROP_TABLE = "DROP_TABLE"
    RENAME_TABLE = "RENAME_TABLE"
    # DML
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    # INDEX
    CREATE_INDEX = "CREATE_INDEX"
    DROP_INDEX = "DROP_INDEX"
    ALTER_INDEX = "ALTER_INDEX"


@dataclass
class SQLOperation:
    """SQL 操作结构化信息"""
    operation_type: str
    sql_type: str
    table_name: Optional[str] = None
    columns: List[str] = None
    conditions: Optional[str] = None
    raw_sql: str = ""
    
    def __post_init__(self):
        if self.columns is None:
            self.columns = []


@dataclass
class ValidationResult:
    """SQL 验证结果"""
    is_valid: bool
    errors: List[str]
    sql_type: str
    operations: List[Dict[str, Any]]
    execution_test: Optional[Dict[str, Any]] = None


class SQLParser:
    """SQL 语句解析器"""
    
    @staticmethod
    def parse_sql_type(sql: str) -> SQLType:
        """识别 SQL 类型"""
        sql_upper = sql.strip().upper()
        
        # DDL 操作
        if any(sql_upper.startswith(op) for op in ['CREATE TABLE', 'ALTER TABLE', 'DROP TABLE', 'RENAME TABLE']):
            return SQLType.DDL
        
        # 索引操作
        if any(sql_upper.startswith(op) for op in ['CREATE INDEX', 'CREATE UNIQUE INDEX', 'DROP INDEX', 'ALTER INDEX']):
            return SQLType.INDEX
        
        # DML 操作
        if any(sql_upper.startswith(op) for op in ['INSERT', 'UPDATE', 'DELETE']):
            return SQLType.DML
        
        return SQLType.UNKNOWN
    
    @staticmethod
    def extract_table_name(sql: str) -> Optional[str]:
        """提取表名"""
        sql_upper = sql.strip().upper()
        
        # CREATE TABLE
        match = re.search(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?`?(\w+)`?', sql_upper, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # ALTER TABLE
        match = re.search(r'ALTER\s+TABLE\s+`?(\w+)`?', sql_upper, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # DROP TABLE
        match = re.search(r'DROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?`?(\w+)`?', sql_upper, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # RENAME TABLE
        match = re.search(r'RENAME\s+TABLE\s+`?(\w+)`?', sql_upper, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # INSERT/UPDATE/DELETE
        match = re.search(r'(?:INSERT\s+INTO|UPDATE|DELETE\s+FROM)\s+`?(\w+)`?', sql_upper, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # INDEX
        match = re.search(r'(?:CREATE|DROP|ALTER)\s+(?:UNIQUE\s+)?INDEX\s+\w+\s+ON\s+`?(\w+)`?', sql_upper, re.IGNORECASE)
        if match:
            return match.group(1)
        
        return None
    
    @staticmethod
    def extract_columns(sql: str, operation_type: str) -> List[str]:
        """提取涉及的列名"""
        columns = []
        sql_upper = sql.upper()
        
        if operation_type == "ALTER_TABLE":
            # ADD COLUMN
            matches = re.findall(r'ADD\s+(?:COLUMN\s+)?`?(\w+)`?', sql_upper, re.IGNORECASE)
            columns.extend(matches)
            # MODIFY COLUMN
            matches = re.findall(r'MODIFY\s+(?:COLUMN\s+)?`?(\w+)`?', sql_upper, re.IGNORECASE)
            columns.extend(matches)
            # DROP COLUMN
            matches = re.findall(r'DROP\s+(?:COLUMN\s+)?`?(\w+)`?', sql_upper, re.IGNORECASE)
            columns.extend(matches)
        
        elif operation_type == "INSERT":
            # INSERT INTO table (col1, col2)
            match = re.search(r'\(([^)]+)\)\s*VALUES', sql_upper, re.IGNORECASE)
            if match:
                cols = match.group(1).split(',')
                columns = [col.strip().strip('`') for col in cols]
        
        elif operation_type == "UPDATE":
            # UPDATE table SET col1=val1, col2=val2
            matches = re.findall(r'SET\s+`?(\w+)`?\s*=', sql_upper, re.IGNORECASE)
            columns.extend(matches)
        
        return columns
    
    @staticmethod
    def extract_conditions(sql: str) -> Optional[str]:
        """提取 WHERE 条件"""
        match = re.search(r'WHERE\s+(.+?)(?:;|$)', sql, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        return None
    
    @staticmethod
    def determine_operation_type(sql: str) -> str:
        """确定操作类型"""
        sql_upper = sql.strip().upper()
        
        if sql_upper.startswith('CREATE TABLE'):
            return OperationType.CREATE_TABLE.value
        elif sql_upper.startswith('ALTER TABLE'):
            return OperationType.ALTER_TABLE.value
        elif sql_upper.startswith('DROP TABLE'):
            return OperationType.DROP_TABLE.value
        elif sql_upper.startswith('RENAME TABLE'):
            return OperationType.RENAME_TABLE.value
        elif sql_upper.startswith('INSERT'):
            return OperationType.INSERT.value
        elif sql_upper.startswith('UPDATE'):
            return OperationType.UPDATE.value
        elif sql_upper.startswith('DELETE'):
            return OperationType.DELETE.value
        elif 'CREATE' in sql_upper and 'INDEX' in sql_upper:
            return OperationType.CREATE_INDEX.value
        elif sql_upper.startswith('DROP INDEX'):
            return OperationType.DROP_INDEX.value
        elif sql_upper.startswith('ALTER INDEX'):
            return OperationType.ALTER_INDEX.value
        
        return "UNKNOWN"
    
    @classmethod
    def parse_sql(cls, sql: str) -> SQLOperation:
        """解析单条 SQL 语句"""
        sql_type = cls.parse_sql_type(sql)
        operation_type = cls.determine_operation_type(sql)
        table_name = cls.extract_table_name(sql)
        columns = cls.extract_columns(sql, operation_type)
        conditions = cls.extract_conditions(sql)
        
        return SQLOperation(
            operation_type=operation_type,
            sql_type=sql_type.value,
            table_name=table_name,
            columns=columns,
            conditions=conditions,
            raw_sql=sql.strip()
        )


class LiquibaseValidator:
    """Liquibase SQL 验证器"""
    
    @staticmethod
    def validate_sql_syntax(sql: str) -> tuple[bool, List[str]]:
        """验证 SQL 语法（使用 Liquibase）"""
        errors = []
        
        # 基本语法检查
        if not sql or not sql.strip():
            errors.append("SQL 语句不能为空")
            return False, errors
        
        # 检查是否包含分号
        if not sql.strip().endswith(';'):
            errors.append("SQL 语句应该以分号结尾")
        
        # 检查括号匹配
        if sql.count('(') != sql.count(')'):
            errors.append("括号不匹配")
        
        # 检查引号匹配
        single_quotes = sql.count("'") - sql.count("\\'")
        if single_quotes % 2 != 0:
            errors.append("单引号不匹配")
        
        # 尝试创建 Liquibase changeset（模拟）
        try:
            # 这里应该调用实际的 Liquibase CLI 或 API
            # 简化示例：检查关键字
            keywords = ['SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE', 
                       'CREATE', 'ALTER', 'DROP', 'TABLE', 'INDEX']
            sql_upper = sql.upper()
            has_keyword = any(keyword in sql_upper for keyword in keywords)
            
            if not has_keyword:
                errors.append("未识别的 SQL 语句类型")
        except Exception as e:
            errors.append(f"Liquibase 验证失败: {str(e)}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def generate_liquibase_changeset(operation: SQLOperation, change_id: str) -> str:
        """生成 Liquibase changeset XML"""
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<databaseChangeLog
    xmlns="http://www.liquibase.org/xml/ns/dbchangelog"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.liquibase.org/xml/ns/dbchangelog
    http://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-4.0.xsd">
    
    <changeSet id="{change_id}" author="sql-validator">
        <sql>
            {operation.raw_sql}
        </sql>
    </changeSet>
</databaseChangeLog>
"""
        return xml


class MCPSQLExecutor:
    """MCP SQL 执行器（模拟）"""
    
    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
    
    def execute_sql(self, sql: str) -> Dict[str, Any]:
        """执行 SQL 语句"""
        # 实际应该调用 MCP SQL 服务
        # 这里是模拟实现
        try:
            print(f"[MCP] 执行 SQL: {sql[:100]}...")
            
            # 模拟执行结果
            result = {
                "success": True,
                "affected_rows": 0,
                "execution_time_ms": 50,
                "message": "SQL 执行成功"
            }
            
            # 根据 SQL 类型模拟不同的影响行数
            if "INSERT" in sql.upper():
                result["affected_rows"] = 1
            elif "UPDATE" in sql.upper():
                result["affected_rows"] = 5
            elif "DELETE" in sql.upper():
                result["affected_rows"] = 3
            
            return result
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"SQL 执行失败: {str(e)}"
            }
    
    def get_table_snapshot(self, table_name: str) -> Dict[str, Any]:
        """获取表快照"""
        # 实际应该查询表的数据
        # 这里返回模拟数据
        return {
            "table_name": table_name,
            "row_count": 100,
            "checksum": "abc123def456",
            "timestamp": "2025-11-18T10:00:00"
        }
    
    def compare_snapshots(self, snapshot1: Dict, snapshot2: Dict) -> bool:
        """比较两个快照是否相同"""
        return snapshot1.get("checksum") == snapshot2.get("checksum")


class SQLValidationAgent:
    """SQL 验证智能体"""
    
    def __init__(self, db_config: Dict[str, str]):
        self.parser = SQLParser()
        self.validator = LiquibaseValidator()
        self.executor = MCPSQLExecutor(db_config)
        self.db_config = db_config
    
    def validate_and_test(self, update_sql: str, rollback_sql: str) -> ValidationResult:
        """验证并测试 SQL"""
        errors = []
        operations = []
        
        # 1. 验证 UPDATE SQL 语法
        is_valid_update, update_errors = self.validator.validate_sql_syntax(update_sql)
        if not is_valid_update:
            errors.extend([f"UPDATE SQL 错误: {e}" for e in update_errors])
        
        # 2. 验证 ROLLBACK SQL 语法
        is_valid_rollback, rollback_errors = self.validator.validate_sql_syntax(rollback_sql)
        if not is_valid_rollback:
            errors.extend([f"ROLLBACK SQL 错误: {e}" for e in rollback_errors])
        
        # 3. 解析 SQL 操作
        update_operation = self.parser.parse_sql(update_sql)
        rollback_operation = self.parser.parse_sql(rollback_sql)
        
        operations.append(asdict(update_operation))
        operations.append(asdict(rollback_operation))
        
        # 4. 确定整体 SQL 类型
        sql_type = update_operation.sql_type
        
        # 5. 如果语法验证通过，执行测试
        execution_test = None
        if is_valid_update and is_valid_rollback:
            execution_test = self._execute_test_cycle(
                update_sql, 
                rollback_sql, 
                update_operation.table_name
            )
            
            if not execution_test["rollback_verified"]:
                errors.append("回滚验证失败: 数据未能还原到初始状态")
        
        # 6. 生成结果
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            sql_type=sql_type,
            operations=operations,
            execution_test=execution_test
        )
    
    def _execute_test_cycle(self, update_sql: str, rollback_sql: str, 
                           table_name: Optional[str]) -> Dict[str, Any]:
        """执行测试周期：更新 -> 回滚 -> 验证"""
        test_result = {
            "initial_snapshot": None,
            "after_update_snapshot": None,
            "after_rollback_snapshot": None,
            "update_result": None,
            "rollback_result": None,
            "rollback_verified": False
        }
        
        try:
            # 1. 获取初始快照
            if table_name:
                test_result["initial_snapshot"] = self.executor.get_table_snapshot(table_name)
            
            # 2. 执行 UPDATE SQL
            print("\n[测试] 执行 UPDATE SQL...")
            test_result["update_result"] = self.executor.execute_sql(update_sql)
            
            if not test_result["update_result"]["success"]:
                return test_result
            
            # 3. 获取更新后快照
            if table_name:
                test_result["after_update_snapshot"] = self.executor.get_table_snapshot(table_name)
            
            # 4. 执行 ROLLBACK SQL
            print("[测试] 执行 ROLLBACK SQL...")
            test_result["rollback_result"] = self.executor.execute_sql(rollback_sql)
            
            if not test_result["rollback_result"]["success"]:
                return test_result
            
            # 5. 获取回滚后快照
            if table_name:
                test_result["after_rollback_snapshot"] = self.executor.get_table_snapshot(table_name)
                
                # 6. 验证回滚是否成功
                test_result["rollback_verified"] = self.executor.compare_snapshots(
                    test_result["initial_snapshot"],
                    test_result["after_rollback_snapshot"]
                )
            else:
                # 如果没有表名（如索引操作），假设回滚成功
                test_result["rollback_verified"] = True
            
        except Exception as e:
            test_result["error"] = str(e)
        
        return test_result


# 使用示例
def main():
    """主函数示例"""
    
    # 数据库配置
    db_config = {
        "username": "test_user",
        "password": "test_pass",
        "url": "jdbc:mysql://localhost:3306/testdb"
    }
    
    # SQL 语句
    sql_config = {
        "update": "UPDATE users SET status = 'active' WHERE id = 1;",
        "rollback": "UPDATE users SET status = 'inactive' WHERE id = 1;"
    }
    
    # 创建智能体
    agent = SQLValidationAgent(db_config)
    
    # 验证和测试
    result = agent.validate_and_test(
        update_sql=sql_config["update"],
        rollback_sql=sql_config["rollback"]
    )
    
    # 输出结果
    result_dict = {
        "is_valid": result.is_valid,
        "errors": result.errors,
        "sql_type": result.sql_type,
        "operations": result.operations,
        "execution_test": result.execution_test
    }
    
    print("\n" + "="*60)
    print("验证结果:")
    print("="*60)
    print(json.dumps(result_dict, indent=2, ensure_ascii=False))
    
    return result_dict


if __name__ == "__main__":
    main()