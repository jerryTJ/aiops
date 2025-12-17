import contextlib
import logging
from collections.abc import AsyncIterator
from typing import Any
from database_tools.tools.event_store import InMemoryEventStore
import click
import json
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Mount
from starlette.types import Receive, Scope, Send
from database_tools.tools.liqubase import LiquibaseUtils, DatabaseUtil

# 配置日志
logger = logging.getLogger(__name__)


@click.command()
@click.option("--port", default=3000, help="Port to listen on for HTTP")
@click.option(
    "--log-level",
    default="INFO",
    help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
)
@click.option(
    "--json-response",
    is_flag=True,
    default=False,
    help="Enable JSON responses instead of SSE streams",
)
def main(port: int, log_level: str, json_response: bool,) -> int:
    # 配置日志
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    app = Server("mcp-streamable")

    @app.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.ContentBlock]:
        ctx = app.request_context
        
        if name == "validate-liquibase-script":
            liquibase_script = arguments.get("liquibase_script")
            db_config = arguments.get("db_config")

            # 发送指定数量的通知
            await ctx.session.send_log_message(
                    level="info",
                    data=f"执行liquibase changeset {liquibase_script}",
                    logger="notification_stream",
                    related_request_id=ctx.request_id,
                )
            logger.debug(f"execute changeSet {liquibase_script}")

            liquibaseTool = LiquibaseUtils(db_config=db_config, liquibase_script=liquibase_script)
            result = liquibaseTool.execute_liquibase()
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(result),
                )
            ]
        elif name == "check-liquibase":
            change_sets = arguments.get("change_sets")
            db_config = arguments.get("db_config")

            # 发送指定数量的通知
            await ctx.session.send_log_message(
                    level="info",
                    data=f"执行liquibase changeset {change_sets}",
                    logger="notification_stream",
                    related_request_id=ctx.request_id,
                )
            logger.debug(f"execute changeSet {change_sets}")

            liquibaseTool = LiquibaseUtils(db_config=db_config, liquibase_script=change_sets)
            result = liquibaseTool.check_changeset()
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(result),
                )
            ]
        elif name == "query-affected-data-of-update":
            # 处理数据库查询
            query_sql = arguments.get("query_sql")
            db_config = arguments.get("db_config", None)
            
            # 发送查询开始日志
            await ctx.session.send_log_message(
                level="info",
                data=f"Executing database query: {query_sql} with db {db_config}",
                logger="database",
                related_request_id=ctx.request_id,
            )
            
            try:
                # 执行数据库查询
                db = DatabaseUtil(db_config)
                result = db.query_result_of_prod_by_sql(query_sql)
                
                # 发送查询完成日志
                await ctx.session.send_log_message(
                    level="info",
                    data=f"查询完成，发现{result['count']}条记录",
                    logger="database",
                    related_request_id=ctx.request_id,
                )
                
                return [types.TextContent(type="text", text=json.dumps(result))]
                
            except Exception as e:
                error_msg = f"Database query failed: {str(e)}"
                await ctx.session.send_log_message(
                    level="error",
                    data=error_msg,
                    logger="database",
                    related_request_id=ctx.request_id,
                )
                return [types.TextContent(type="text", text=error_msg)]
        elif name == "create_change_id":
            # 处理数据库查询
            db_name = arguments.get("db_name")
            
            # 发送查询开始日志
            await ctx.session.send_log_message(
                level="info",
                data="生成唯一的changeSetId",
                logger="database",
                related_request_id=ctx.request_id,
            )
            
            try:
                # 执行数据库查询
                result = LiquibaseUtils.create_liquibase_change_id(db_name)
                
                # 发送查询完成日志
                await ctx.session.send_log_message(
                    level="info",
                    data=f"changeSet Id 生成完成{result['change_id']}",
                    logger="database",
                    related_request_id=ctx.request_id,
                )
                
                result_text = json.dumps(result)
                return [types.TextContent(type="text", text=result_text)]
                
            except Exception as e:
                error_msg = f"create changeSet Id failed: {str(e)}"
                await ctx.session.send_log_message(
                    level="error",
                    data=error_msg,
                    logger="database",
                    related_request_id=ctx.request_id,
                )
                return [types.TextContent(type="text", text=error_msg)]
        else:
            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="validate-liquibase-script",
                description=("验证生成的changeSet是否能正确执行(更新和回滚)"),
                strict=True,
                inputSchema={
                    "type": "object",
                    "required": ["liquibase_script", "db_config"],
                    "properties": {
                        "liquibase_script": {
                            "type": "string",
                            "description": """包含更新和回滚sql的changeSet 示例如下:
--liquibase formatted sql
--changeset zhangsan:T1-20251125-001 context:prod
--comment: 更新用户昵称
UPDATE t_users SET nick_name='Tom', open_id=1 WHERE id=1;
--rollback UPDATE t_users SET nick_name='Jerry', open_id=2 WHERE id=1""",
                        },
                        "db_config": {
                            "type": "string",
                            "description": "数据库配置的json串(数据库地址、用户和密码){'db_url':'localhost:3306','db_name':'applier','username':'root', 'pwd':'Admin@123'}",
                        }
                    },
                },
            ),
            types.Tool(
                name="query-affected-data-of-update",
                description="查询变更sql对应的查询语句影响的行数，为回滚作准备",
                strict=True,
                inputSchema={
                    "type": "object",
                    "required": ["query_sql", "db_config"],
                    "properties": {
                        "query_sql": {
                            "type": "string",
                            "description": "查询更新语句影响的数据量"
                        },
                         "db_config": {
                            "type": "string",
                            "description": "数据库配置{'db_url':'localhost:3306','db_name':'applier','username':'readonly', 'pwd':'Admin@123'}",
                        }
                    },
                },
            ),
            types.Tool(
                name="create_change_id",
                description="在同一个变更的数据库中保持唯一的id",
                strict=True,
                inputSchema={
                    "type": "object",
                    "required": ["db_name"],
                    "properties": {
                        "db_name": {
                            "type": "string",
                            "description": "变更的数据库名称"
                        }
                    },
                },
            )
        ]

    # 创建事件存储（用于恢复）
    event_store = InMemoryEventStore()

    # 创建会话管理器
    session_manager = StreamableHTTPSessionManager(
        app=app,
        event_store=event_store,  # 启用恢复功能
        json_response=json_response,
    )

    # ASGI 处理器
    async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
        await session_manager.handle_request(scope, receive, send)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        """管理会话管理器生命周期"""
        async with session_manager.run():
            logger.info("Application started with StreamableHTTP session manager!")
            try:
                yield
            finally:
                logger.info("Application shutting down...")

    # 创建 ASGI 应用
    starlette_app = Starlette(
        debug=True,
        routes=[
            Mount("/mcp", app=handle_streamable_http),
        ],
        lifespan=lifespan,
    )

    # 添加 CORS 中间件
    starlette_app = CORSMiddleware(
        starlette_app,
        allow_origins=["*"],
        allow_methods=["GET", "POST", "DELETE"],
        expose_headers=["Mcp-Session-Id"],
    )

    import uvicorn

    uvicorn.run(starlette_app, host="127.0.0.1", port=port)

    return 0


if __name__ == "__main__":
    main()
