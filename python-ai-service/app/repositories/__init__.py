"""
数据访问层 (Repository Pattern)。

封装数据库 CRUD 操作，为 Service 层提供数据访问接口。
"""

# 当前阶段: 数据访问由 SQLAlchemy ORM + MyBatis Plus (Java) 协作完成
# Python 侧主要读写 Prompt 模板、系统配置等轻量数据
# 后续可在此目录下扩展各实体的 Repository 类
