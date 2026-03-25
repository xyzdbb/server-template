# 架构说明文档

> 本文档详细描述项目的技术架构、设计决策和实现细节，供开发者深入理解和扩展使用。

---

## 目录

- [系统概览](#系统概览)
- [分层架构](#分层架构)
- [请求生命周期](#请求生命周期)
- [模块结构](#模块结构)
- [核心基础设施](#核心基础设施)
- [认证与授权](#认证与授权)
- [数据访问层](#数据访问层)
- [中间件链](#中间件链)
- [异常处理](#异常处理)
- [配置管理](#配置管理)
- [测试架构](#测试架构)
- [部署架构](#部署架构)
- [设计决策记录](#设计决策记录)

---

## 系统概览

```
┌─────────────────────────────────────────────────────────────────┐
│                        客户端 (Browser / App)                    │
└───────────────────────────────┬──────────────────────────────────┘
                                │ HTTPS
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    反向代理 (Nginx / ALB / Cloudflare)           │
│                    (TLS 终止, HSTS, 负载均衡)                     │
└───────────────────────────────┬──────────────────────────────────┘
                                │ HTTP
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI 应用 (gunicorn + uvicorn worker)      │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    中间件链 (LIFO)                         │  │
│  │  ProxyHeaders → RequestID → Security → Logging → CORS     │  │
│  └─────────────────────────┬─────────────────────────────────┘  │
│                            ▼                                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              API Router (/api/v1/)                         │  │
│  │  auth / users / items / health                            │  │
│  └─────────────────────────┬─────────────────────────────────┘  │
│                            ▼                                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              Service 层 (业务逻辑)                          │  │
│  └──────────────┬──────────────────────────┬─────────────────┘  │
│                 ▼                          ▼                     │
│  ┌──────────────────────┐   ┌──────────────────────────────┐   │
│  │  Repository 层 (数据) │   │  Redis (Token / Rate Limit)  │   │
│  └──────────┬───────────┘   └──────────────────────────────┘   │
│             ▼                                                    │
│  ┌──────────────────────┐                                       │
│  │  PostgreSQL (持久化)  │                                       │
│  └──────────────────────┘                                       │
└─────────────────────────────────────────────────────────────────┘
```

### 技术栈

| 组件 | 技术选型 | 版本要求 | 用途 |
|------|----------|----------|------|
| 运行时 | Python | >= 3.12 | 现代类型语法 (`X \| None`, `type` 语句) |
| Web 框架 | FastAPI | >= 0.115 | HTTP 路由、依赖注入、OpenAPI |
| ORM | SQLModel | >= 0.0.22 | Pydantic + SQLAlchemy 融合 |
| 数据库 | PostgreSQL | 16 | 主存储 |
| 缓存/会话 | Redis | 7 | Token 撤销、频率限制计数器 |
| 迁移 | Alembic | >= 1.13 | 数据库 Schema 版本管理 |
| 认证 | PyJWT + bcrypt | — | JWT 签发/验证、密码哈希 |
| 包管理 | uv | — | 极速依赖解析与安装 |
| 部署 | Docker + gunicorn | — | 多阶段构建、多 worker 进程 |

---

## 分层架构

项目采用**四层分离架构**，每一层有明确的职责边界和禁止事项：

```
┌──────────────────────────────────────────────────────┐
│  Endpoint 层 (app/api/v1/endpoints/)                 │
│  职责: HTTP 参数解析、调用 Service、返回响应模型        │
│  禁止: 业务逻辑、直接数据库操作、Redis 操作             │
├──────────────────────────────────────────────────────┤
│  Service 层 (app/modules/*/service.py)               │
│  职责: 业务规则、权限校验、事务管理、跨仓储编排          │
│  禁止: HTTP 请求/响应操作                              │
├──────────────────────────────────────────────────────┤
│  Repository 层 (app/modules/*/repository.py)         │
│  职责: 数据查询、过滤、持久化 (flush，不 commit)        │
│  禁止: 权限判断、HTTP 异常、Redis 操作                  │
├──────────────────────────────────────────────────────┤
│  Model 层 (app/modules/*/models.py)                  │
│  职责: 数据库表映射（SQLModel ORM）                     │
│  禁止: 业务逻辑                                       │
└──────────────────────────────────────────────────────┘
```

### 层间数据流

```
Endpoint                 Service                  Repository              Database
   │                        │                         │                      │
   │  UserCreate (schema)   │                         │                      │
   ├───────────────────────►│                         │                      │
   │                        │  validate password      │                      │
   │                        │  check duplicate        │                      │
   │                        ├────────────────────────►│  SELECT ... WHERE    │
   │                        │                         ├─────────────────────►│
   │                        │                         │◄─────────────────────┤
   │                        │◄────────────────────────┤  User | None         │
   │                        │                         │                      │
   │                        │  hash password          │                      │
   │                        │  create({...})          │                      │
   │                        ├────────────────────────►│  INSERT + flush()    │
   │                        │                         ├─────────────────────►│
   │                        │                         │◄─────────────────────┤
   │                        │◄────────────────────────┤  User (flushed)      │
   │                        │                         │                      │
   │                        │  commit_and_refresh()   │                      │
   │                        ├─────────────────────────┼─────────────────────►│
   │                        │                         │                      │
   │  User (ORM instance)   │                         │                      │
   │◄───────────────────────┤                         │                      │
   │                        │                         │                      │
   │  UserResponse (schema) │                         │                      │
   │  ← response_model 自动转换                        │                      │
```

### 事务管理策略

```python
# Repository 层: flush (写入但不提交)
session.add(db_obj)
session.flush()  # 分配 ID，但事务未提交

# Service 层: commit (统一提交)
commit_and_refresh(session, instance)  # commit + refresh，异常自动 rollback
```

这确保了：
- 一个 Service 方法内的多个 Repository 操作在同一事务中
- 任何环节失败，整个事务回滚
- Repository 层可以独立测试（flush 后可查询但不影响其他测试）

---

## 请求生命周期

一个典型的 `POST /api/v1/items/` 请求经历以下阶段：

```
1. 客户端发送 HTTP POST 请求

2. 中间件链 (外 → 内):
   ┌─ ProxyHeadersMiddleware ── 从 X-Forwarded-For 解析真实 IP
   │  ┌─ RequestIDMiddleware ── 生成 UUID，写入 ContextVar
   │  │  ┌─ SecurityHeadersMiddleware ── 注入安全响应头
   │  │  │  ┌─ LoggingMiddleware ── 开始计时
   │  │  │  │  ┌─ CORSMiddleware ── 处理 CORS 预检/响应头
   │  │  │  │  │
   │  │  │  │  │  3. ErrorHandler (exception_handler):
   │  │  │  │  │     注册 AppException → JSON 响应映射
   │  │  │  │  │
   │  │  │  │  │  4. 路由匹配: /api/v1/items/ → items.create_new_item
   │  │  │  │  │
   │  │  │  │  │  5. 依赖注入解析:
   │  │  │  │  │     SessionDep  → get_session() → Session
   │  │  │  │  │     TokenDep    → OAuth2PasswordBearer → "Bearer xxx"
   │  │  │  │  │     CurrentUser → decode_token + get user from DB
   │  │  │  │  │     ItemCreate  → JSON body validation
   │  │  │  │  │
   │  │  │  │  │  6. Endpoint 执行:
   │  │  │  │  │     create_item(session, item_in, owner_id=user.pk)
   │  │  │  │  │       → item_repository.create(session, data)  # flush
   │  │  │  │  │       → commit_and_refresh(session, item)      # commit
   │  │  │  │  │
   │  │  │  │  │  7. 响应序列化: Item → ItemResponse (response_model)
   │  │  │  │  │
   │  │  │  │  └─ CORS 响应头注入
   │  │  │  └─ 记录日志: method=POST path=/api/v1/items/ status=201 duration=0.045s
   │  │  └─ 安全响应头注入
   │  └─ X-Request-Id 响应头注入
   └─ 完成

8. 客户端收到 201 Created + JSON body
```

---

## 模块结构

### 模块文件布局

每个业务模块遵循统一的文件结构：

```
app/modules/<name>/
├── __init__.py        # 模块标识
├── models.py          # SQLModel ORM 模型 (继承 TableBase)
├── schemas.py         # Pydantic 请求/响应模型
├── repository.py      # 数据访问层 (继承 RepositoryBase[Model])
├── service.py         # 业务逻辑层
└── deps.py            # 可选: 模块专用依赖 (如列表查询参数)
```

对应的 endpoint 位于 `app/api/v1/endpoints/<name>.py`，在 `app/api/v1/router.py` 中注册。

### 当前模块

```
┌─────────────────────────────────────────────────────────────┐
│                        模块关系图                             │
│                                                              │
│  ┌─────────┐     ┌─────────┐     ┌─────────────────────┐   │
│  │  auth   │────►│  users  │     │  items              │   │
│  │         │     │         │     │                     │   │
│  │ 无 model │     │ User    │◄────│ Item.owner_id (FK)  │   │
│  │ 无 repo  │     │ UserRepo│     │ ItemRepo            │   │
│  │ service │     │ service │     │ service             │   │
│  └─────────┘     └─────────┘     └─────────────────────┘   │
│                                                              │
│  auth 模块调用 user_repository 验证用户身份                    │
│  items 通过 owner_id 外键关联 users                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 核心基础设施

### 依赖注入链

```python
# app/api/deps.py — 层层叠加的依赖

get_session()          # Generator[Session] — 数据库会话
    ↓
SessionDep = Annotated[Session, Depends(get_session)]

OAuth2PasswordBearer   # 从 Authorization header 提取 token
    ↓
TokenDep = Annotated[str, Depends(oauth2_scheme)]

get_current_user(SessionDep, TokenDep)  # 解码 token → 查询用户
    ↓
CurrentUser = Annotated[User, Depends(get_current_user)]

get_current_superuser(CurrentUser)  # 检查 is_superuser
    ↓
CurrentSuperuser = Annotated[User, Depends(get_current_superuser)]
```

### 泛型分页响应

```python
# app/schemas/common.py

class Page(BaseModel, Generic[T]):
    items: list[T]       # 当前页数据
    total: int           # 总记录数
    skip: int            # 跳过记录数
    limit: int           # 每页大小

    # 计算属性 (自动包含在 JSON 响应中)
    current_page: int    # 当前页码 (1-based)
    total_pages: int     # 总页数
    has_next: bool       # 是否有下一页
    has_previous: bool   # 是否有上一页

# 使用方式 (endpoint):
Page[UserResponse]       # → {"items": [...], "total": 42, "current_page": 1, ...}
Page[ItemResponse]       # 同一 Page 模板适配不同资源
```

---

## 认证与授权

### JWT 双 Token 机制

```
┌────────────────────────────────────────────────────────────┐
│                    Token 类型对比                            │
├─────────────┬──────────────────┬───────────────────────────┤
│             │  Access Token    │  Refresh Token            │
├─────────────┼──────────────────┼───────────────────────────┤
│ 有效期       │ 30 分钟          │ 7 天                      │
│ 存储位置     │ 客户端内存        │ 客户端持久存储             │
│ 用途         │ API 鉴权         │ 换取新 token 对            │
│ 是否可撤销   │ 否 (无状态)      │ 是 (Redis jti 追踪)       │
│ payload.type │ "access"        │ "refresh"                 │
│ payload.jti  │ 无              │ 有 (唯一标识)              │
└─────────────┴──────────────────┴───────────────────────────┘
```

### Token 流转

```
登录:
  Client → POST /auth/login {username, password}
  Server → 验证密码 → 签发 access_token + refresh_token
         → Redis SET refresh_token:{jti} = user_id (TTL=7天)
  Client ← {access_token, refresh_token}

刷新:
  Client → POST /auth/refresh {refresh_token}
  Server → 解码 token → Redis EXISTS refresh_token:{old_jti}
         → Redis DEL refresh_token:{old_jti}     ← 旧 token 立即失效
         → 签发新 token 对
         → Redis SET refresh_token:{new_jti}     ← 新 token 入库
  Client ← {new_access_token, new_refresh_token}

登出:
  Client → POST /auth/logout {refresh_token} + Authorization: Bearer access_token
  Server → 校验 token 归属当前用户
         → Redis DEL refresh_token:{jti}
  Client ← 204 No Content
```

### 安全防护措施

1. **时序攻击防护**: 用户不存在时仍执行 `bcrypt.checkpw(password, DUMMY_HASH)`
2. **Token 类型隔离**: `decode_token(token, expected_type="access")` 防止 refresh token 混用
3. **Token 归属校验**: logout 时验证 refresh token 的 `sub` 与当前用户一致
4. **Refresh token 一次性使用**: 刷新后旧 jti 立即从 Redis 删除

---

## 数据访问层

### TableBase — 所有模型的基类

```python
class TableBase(SQLModel):
    id: int | None          # 主键，插入前为 None
    created_at: datetime    # UTC 创建时间
    updated_at: datetime    # UTC 更新时间 (onupdate 自动刷新)
    deleted_at: datetime | None  # 软删除时间戳，None = 未删除

    @property
    def pk(self) -> int:    # 安全获取主键，未持久化时抛 RuntimeError
```

### RepositoryBase[ModelType] — 泛型仓储基类

提供以下标准操作，所有查询自动过滤 `deleted_at IS NULL`：

| 方法 | 用途 | 备注 |
|------|------|------|
| `get(session, id)` | 按主键查询 | 返回 `ModelType \| None` |
| `get_multi(session, skip, limit, sort_by, sort_order)` | 分页列表 | 支持排序 |
| `count(session)` | 计数 | 不含软删除记录 |
| `create(session, obj_in)` | 创建 | flush，不 commit |
| `update(session, db_obj, obj_in)` | 更新 | 自动跳过 protected_fields |
| `soft_delete(session, target)` | 软删除 | 设置 deleted_at |

子类通过 `_build_filtered_statement()` 模式扩展查询条件：

```python
class ItemRepository(RepositoryBase[Item]):
    def _build_filtered_statement(self, owner_id=None, search=None):
        statement = select(Item).where(Item.deleted_at.is_(None))
        if owner_id is not None:
            statement = statement.where(Item.owner_id == owner_id)
        if search:
            statement = statement.where(
                Item.title.ilike(f"%{self._escape_like(search)}%")
            )
        return statement
```

---

## 中间件链

注册顺序与实际执行顺序相反 (Starlette LIFO)：

```python
# main.py 中注册顺序 (后注册先执行):
app.add_middleware(LoggingMiddleware)            # 4. 记录请求日志
app.add_middleware(SecurityHeadersMiddleware)     # 3. 注入安全头
app.add_middleware(RequestIDMiddleware)           # 2. 生成请求 ID
app.add_middleware(ProxyHeadersMiddleware, ...)   # 1. 解析真实 IP
```

实际执行顺序：

```
请求 → ProxyHeaders → RequestID → SecurityHeaders → Logging → CORS → [路由处理]
响应 ← ProxyHeaders ← RequestID ← SecurityHeaders ← Logging ← CORS ← [路由处理]
```

| 中间件 | 文件 | 职责 |
|--------|------|------|
| ProxyHeadersMiddleware | uvicorn 内置 | 从 `X-Forwarded-For` 解析真实客户端 IP |
| RequestIDMiddleware | `middleware/request_id.py` | 生成 UUID，写入 ContextVar + 响应头 |
| SecurityHeadersMiddleware | `middleware/security.py` | 注入 X-Content-Type-Options 等安全头 |
| LoggingMiddleware | `middleware/logging.py` | JSON 格式记录请求方法/路径/状态码/耗时 |
| CORSMiddleware | FastAPI 内置 | 处理跨域请求 |

所有自定义中间件使用原始 ASGI 协议实现（非 Starlette BaseHTTPMiddleware），性能更好。

---

## 异常处理

### 异常层次

```
AppException (400)
├── ValidationException (400)  — 业务校验失败
├── AuthException (401)        — 认证失败
├── PermissionDeniedException (403) — 权限不足
├── NotFoundException (404)    — 资源不存在
├── ConflictException (409)    — 资源冲突
└── DatabaseException (503)    — 数据库异常
```

### 处理流程

```python
# 业务代码只需抛异常:
raise NotFoundException("Item not found")

# error_handler.py 自动转换:
# → HTTP 404 {"detail": "Item not found"}

# 未捕获的异常:
# → HTTP 500 {"detail": "Internal server error"} + 错误日志 (含堆栈)
```

---

## 配置管理

`app/core/config.py` 使用 `pydantic-settings` 管理所有配置：

```
优先级 (高 → 低):
  环境变量 > .env 文件 > 代码默认值
```

### 关键配置分组

```
┌─ 基础 ─────────────────────────────────────┐
│  PROJECT_NAME, API_V1_STR, ENVIRONMENT     │
├─ 安全 ─────────────────────────────────────┤
│  SECRET_KEY (必填, ≥32字符)                 │
│  ALGORITHM (HS256)                         │
│  ACCESS_TOKEN_EXPIRE_MINUTES (30)          │
│  REFRESH_TOKEN_EXPIRE_MINUTES (10080)      │
├─ 数据库 ───────────────────────────────────┤
│  POSTGRES_* → computed DATABASE_URL        │
│  (自动 URL-encode 用户名和密码)              │
├─ Redis ────────────────────────────────────┤
│  REDIS_URL (redis://localhost:6379/0)      │
├─ 网络 ─────────────────────────────────────┤
│  TRUSTED_HOSTS (反向代理 IP 列表)           │
│  BACKEND_CORS_ORIGINS (禁止通配符 *)        │
├─ 初始化 ───────────────────────────────────┤
│  FIRST_SUPERUSER, FIRST_SUPERUSER_PASSWORD │
└────────────────────────────────────────────┘
```

---

## 测试架构

### 测试分层

```
tests/
├── api/v1/              # 接口层测试 — 完整 HTTP 请求/响应
│   ├── test_auth.py     # 认证流程 (登录/注册/刷新/登出/Token轮换)
│   ├── test_users.py    # 用户管理 (个人信息/管理员列表/权限)
│   ├── test_items.py    # CRUD + 权限控制 + 分页搜索
│   └── test_health.py   # 健康检查
├── services/            # 服务层测试 — 业务逻辑
│   └── test_user_service.py  # 创建/更新/密码验证/重复检测
└── repositories/        # 仓储层测试 — 数据访问
    └── test_user_repository.py  # CRUD/软删除/查询过滤
```

### 测试基础设施

```
┌─────────────────────────────────────────────────────────────┐
│                    conftest.py 核心 Fixture                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  _pg_container (session scope)                               │
│  └─ testcontainers: PostgresContainer("postgres:16-alpine") │
│     └─ 与生产环境完全一致的 PostgreSQL 实例                    │
│                                                              │
│  _engine (session scope)                                     │
│  └─ create_engine → create_all → 测试结束后 drop_all          │
│                                                              │
│  session (function scope)                                    │
│  └─ 基于事务 + savepoint 的隔离:                               │
│     conn.begin() → Session(join_transaction_mode="...")       │
│     → 测试结束后 txn.rollback() — 数据自动清理                 │
│                                                              │
│  client (function scope)                                     │
│  └─ TestClient(app) + dependency_overrides[get_session]      │
│                                                              │
│  _mock_redis (autouse)                                       │
│  └─ FakeRedis 内存替身 (支持 set/get/exists/delete/ttl)      │
│                                                              │
│  _disable_rate_limit (autouse)                               │
│  └─ limiter.enabled = False — 避免跨用例累积触发 429          │
│                                                              │
│  superuser_headers                                           │
│  └─ 创建超管 + 登录 → 返回 {"Authorization": "Bearer ..."}   │
└─────────────────────────────────────────────────────────────┘
```

### 测试隔离策略

```
每个测试函数:
  1. conn.begin()  ← 开启外层事务
  2. Session(join_transaction_mode="create_savepoint")  ← savepoint 隔离
  3. 测试执行 (所有 DB 操作在 savepoint 内)
  4. txn.rollback()  ← 回滚外层事务，数据库恢复原状
  5. conn.close()

效果: 测试间完全隔离，无数据残留，无需手动清理
```

---

## 部署架构

### Docker 多阶段构建

```
┌─────────────────────────────────────────┐
│          Builder Stage                   │
│  FROM: ghcr.io/astral-sh/uv:python3.12 │
│  步骤: uv sync --no-dev                 │
│  产物: /app/.venv (仅运行时依赖)          │
├─────────────────────────────────────────┤
│          Runtime Stage                   │
│  FROM: python:3.12-slim-bookworm        │
│  COPY: .venv + app/ + alembic/ + scripts│
│  USER: appuser (非 root, uid=1000)      │
│  HEALTHCHECK: curl /api/v1/health       │
│  CMD: entrypoint.sh                     │
└─────────────────────────────────────────┘
```

### 生产启动流程

```bash
# scripts/entrypoint.sh
alembic upgrade head           # 1. 执行数据库迁移
python -m scripts.bootstrap_db # 2. 创建初始超管 (幂等)
gunicorn app.main:app \        # 3. 启动应用
    --workers $WEB_CONCURRENCY \  # 默认 4 进程
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000
```

### Compose 服务编排

```
docker-compose.yml
├── db (postgres:16-alpine)    ← 始终启动，healthcheck
├── redis (redis:7-alpine)     ← 始终启动，requirepass
├── backend-dev  [profile: dev]  ← 挂载源码，uvicorn --reload
└── backend-prod [profile: prod] ← 多阶段构建，gunicorn，restart: always
```

---

## 设计决策记录

### DR-01: 全同步架构

**决策**: 所有 endpoint 使用 `def`（非 `async def`），DB 和 Redis 均为同步客户端。

**原因**:
- 目标场景为中小型项目，并发量不高
- 统一编程模型，无 sync/async 混用的心智负担
- 调试时栈帧清晰，无协程调度干扰
- FastAPI 自动将 `def` endpoint 放入线程池，同步 I/O 不会阻塞事件循环

**迁移路径**: 如需异步化，需整体切换：`create_async_engine` + `AsyncSession` + `redis.asyncio`。

### DR-02: Repository flush + Service commit

**决策**: Repository 层 `session.flush()`，Service 层 `commit_and_refresh()`。

**原因**:
- 一个 Service 方法内可能调用多个 Repository 操作，需要在同一事务中
- flush 后即可获取自增 ID，commit 由 Service 统一控制
- 异常时 `commit_and_refresh` 自动 rollback

### DR-03: 软删除而非物理删除

**决策**: 所有模型的 "删除" 操作设置 `deleted_at` 时间戳。

**原因**:
- 便于数据审计和恢复
- 外键关系不会因删除而断裂
- 所有查询自动过滤 `deleted_at IS NULL`

**代价**: 数据量会持续增长，需要定期归档或建立 partial index。

### DR-04: 模块级 Repository 单例

**决策**: `user_repository = UserRepository(User)` 在模块加载时实例化。

**原因**:
- Repository 无状态（Session 通过参数传入）
- 避免每次请求创建实例的开销
- 简化 Service 层的依赖管理

### DR-05: 自定义 ASGI 中间件

**决策**: RequestID / Logging / Security 中间件直接实现 ASGI 协议，不继承 `BaseHTTPMiddleware`。

**原因**:
- `BaseHTTPMiddleware` 会将整个请求/响应读入内存
- 原始 ASGI 实现更轻量，支持流式处理
- 性能更好，内存占用更低
