# FastAPI 现代化后端项目

基于 FastAPI + SQLModel + PostgreSQL + Docker + uv 的企业级分层架构。

## 数据库策略

项目统一采用 Alembic 管理数据库 schema。

- 所有表结构变更都通过 `alembic revision` 和 `alembic upgrade` 管理
- 应用启动不会自动建表或自动执行迁移
- `scripts/bootstrap_db.py` 只负责初始化业务数据，例如超级管理员
- 测试环境仍使用 `SQLModel.metadata.create_all()` 快速创建内存库

## 快速开始

### Docker 开发

```bash
# 1. 配置环境
cp .env.example .env

# 2. 启动数据库和开发服务
docker compose --profile dev up -d

# 3. 执行 schema 迁移
docker compose exec backend-dev alembic upgrade head

# 4. 初始化业务数据
docker compose exec backend-dev python scripts/bootstrap_db.py

# 5. 访问 API 文档
open http://localhost:8000/docs
```

### 本地开发

```bash
# 1. 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 安装依赖
uv sync

# 3. 启动数据库
docker compose up -d db

# 4. 执行 schema 迁移
uv run alembic upgrade head

# 5. 初始化业务数据
uv run python scripts/bootstrap_db.py

# 6. 启动服务
uv run uvicorn app.main:app --reload
```

## 常用命令

```bash
# 生成迁移
uv run alembic revision --autogenerate -m "describe change"

# 应用最新迁移
uv run alembic upgrade head

# 回滚一步
uv run alembic downgrade -1

# 初始化业务数据
uv run python scripts/bootstrap_db.py
```

## License

MIT