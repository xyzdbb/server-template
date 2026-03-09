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

## 架构说明

项目采用“按业务模块组织 + 模块内分层”的后端架构，目录职责如下：

- `app/main.py`：应用入口，负责组装 FastAPI、CORS、中间件和总路由。
- `app/api/`：接口层，负责路由注册、请求参数解析、响应模型声明、依赖注入和接口文档。
- `app/modules/<module>/schemas.py`：请求/响应 DTO、列表参数模型。
- `app/modules/<module>/models.py`：数据库模型定义。
- `app/modules/<module>/repository.py`：数据访问层，只负责查询、过滤、持久化。
- `app/modules/<module>/service.py`：业务层，负责业务规则、权限判断、事务提交和跨仓储编排。
- `app/core/`：基础设施层，提供配置、数据库、日志、安全、事务等通用能力。
- `app/middleware/`：横切能力，处理请求日志、请求 ID、统一异常响应。
- `scripts/`：运维和初始化脚本，例如初始化超级管理员。
- `tests/`：接口、服务、数据访问测试。

### 架构图文字版

```text
客户端请求
  -> `app/main.py`
  -> 中间件链
     -> `RequestIDMiddleware`
     -> `LoggingMiddleware`
     -> `ErrorHandlerMiddleware`
  -> `app/api/v1/router.py`
  -> 具体 endpoint
     -> `app/api/deps.py`
        -> 提供 Session / Token / CurrentUser / ListParams
     -> `app/modules/*/service.py`
        -> 处理业务规则、权限、事务
     -> `app/modules/*/repository.py`
        -> 执行 SQLModel 查询与持久化
     -> `app/modules/*/models.py`
        -> 映射数据库表
  -> 响应模型返回客户端
```

### 当前模块关系

- `auth`：认证相关能力，负责登录、刷新令牌、解析当前登录用户。
- `users`：用户域能力，负责用户创建、更新、筛选查询、超级管理员创建。
- `items`：示例业务模块，负责当前用户自己的资源增删改查。

### 当前架构优化点

当前版本已经完成以下收敛：

- 将通用事务提交与刷新逻辑下沉到 `app/core/transaction.py`，避免业务模块重复实现。
- 将“根据 access token 获取当前用户”的逻辑收口到 `app/modules/auth/service.py`，减少接口层直接依赖仓储。
- 将“创建超级管理员”抽成独立业务用例，`scripts/bootstrap_db.py` 不再手动拼装提交逻辑。
- 移除包级聚合导出带来的循环导入风险，统一使用显式模块导入。

仍建议后续继续关注：

- 当模块继续增加时，可将 `app/api/deps.py` 拆分为更细的依赖文件，避免持续膨胀。
- 如果后续引入角色、权限、OAuth、租户等能力，可进一步细化 `auth` 与 `users` 的边界。
- `tests/crud/` 建议后续统一命名为 `tests/repositories/`，与运行时代码术语保持一致。

## 新功能开发模板清单

新增一个业务模块时，推荐按下面步骤落地：

1. 在 `app/modules/<module_name>/models.py` 定义数据库模型。
2. 在 `app/modules/<module_name>/schemas.py` 定义 `Create`、`Update`、`Response`、`ListParams` 等模型。
3. 在 `app/modules/<module_name>/repository.py` 编写数据访问逻辑。
4. 在 `app/modules/<module_name>/service.py` 编写业务规则、权限判断、事务处理。
5. 在 `app/api/v1/endpoints/<module_name>.py` 暴露接口，保持 endpoint 足够薄。
6. 在 `app/api/v1/router.py` 注册路由。
7. 如涉及表结构变更，生成并执行 Alembic migration。
8. 在 `tests/` 下补齐接口测试和服务测试。

### 编写约束

- endpoint 只负责接收参数、调用 service、返回响应，不直接写复杂业务。
- repository 只负责数据访问，不处理权限、不拼装 HTTP 异常。
- service 是业务规则的唯一入口，涉及事务提交时优先复用 `app/core/transaction.py`。
- 需要鉴权的接口统一通过 `app/api/deps.py` 获取 `CurrentUser`。
- 公共能力优先放入 `app/core/`、`app/schemas/`、`app/utils/`，不要在业务模块内重复实现。

### 推荐目录模板

```text
app/modules/<module_name>/
  ├── models.py
  ├── schemas.py
  ├── repository.py
  └── service.py
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
