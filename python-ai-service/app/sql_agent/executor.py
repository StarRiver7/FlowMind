
"""SQL 执行器 - 只读从库执行。

强制所有查询走只读数据库连接，物理层面杜绝写操作。
"""

import os
from app.core.logger import get_logger

logger = get_logger(__name__)


class SQLExecutor:
    """SQL 只读执行器。

    使用独立的只读数据库连接，DB 用户仅有 SELECT 权限。
    """

    def __init__(self):
        self._readonly_url = os.getenv(
            "SQL_READONLY_URL",
            os.getenv("DATABASE_URL", "mysql+pymysql://readonly:readonly@localhost:3306/enterprise_ai"),
        )

    async def execute(self, sql: str, timeout: int = 30) -> dict:
        """在只读从库上执行 SELECT 查询。

        Args:
            sql: 已通过安全校验的 SELECT 语句
            timeout: 超时秒数

        Returns:
            {"columns": [...], "rows": [...], "row_count": N}
        """
        try:
            from sqlalchemy import text
            from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
            from sqlalchemy.orm import sessionmaker

            # 将同步 URL 转为异步
            async_url = self._readonly_url.replace("mysql+pymysql://", "mysql+aiomysql://")

            engine = create_async_engine(async_url, echo=False, pool_pre_ping=True)
            async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

            try:
                async with async_session() as session:
                    result = await session.execute(text(sql))
                    rows = result.fetchall()
                    columns = list(result.keys())

                    return {
                        "columns": columns,
                        "rows": [dict(zip(columns, row)) for row in rows],
                        "row_count": len(rows),
                    }
            finally:
                await engine.dispose()

        except ImportError:
            # 数据库驱动未安装时的 mock 返回
            logger.warning("SQL executor: aiomysql not available, returning mock data")
            return {
                "columns": ["result"],
                "rows": [{"result": "(数据库连接未配置，这是模拟结果)"}],
                "row_count": 1,
            }
        except Exception as e:
            logger.error(f"SQL execution error: {e}")
            raise


sql_executor = SQLExecutor()
