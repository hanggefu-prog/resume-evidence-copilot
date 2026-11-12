# AI Recruitment Copilot · AI 招聘助手

一个围绕简历解析、岗位匹配和面试准备构建的全栈 AI 招聘工作台。上传简历与职位描述后，可以查看结构化信息、检索匹配对象、生成带理由的匹配评分，并获取针对候选人的面试问题。

项目适合用于本地体验、全栈 AI 应用学习和功能验证。目前定位为演示与开发项目，尚未提供完整的生产环境用户体系和权限管理。

## 功能概览

| 功能 | 当前实现 |
| --- | --- |
| 简历与岗位录入 | 支持粘贴文本，或上传 PDF、TXT、Markdown 文件；单个文件上限为 5 MB |
| 结构化解析 | 使用大语言模型提取技能、工作年限、岗位要求等字段，并通过 Pydantic 校验 |
| 双向匹配 | 根据岗位查找候选人，也可根据候选人查找岗位 |
| 语义检索与重排 | 使用本地向量模型和 pgvector 召回，再结合技能重合度、经验匹配度排序 |
| 匹配评分 | 为候选人与岗位生成 0–100 分的评估，展示评分理由、匹配技能与缺失技能 |
| 岗位要求与简历原文对照 | 在岗位详情点击候选人旁的「原文对照」，按已解析的必备技能和最低工作年限查看模型判断。点击引文可定位到简历文本；后端逐字核验引文，无法核验的判断标为「待确认」。 |
| 面试题生成 | 根据候选人经历和岗位要求生成 5 个针对性问题 |
| 调用监控 | 展示已记录的模型调用量、成功率、平均耗时、重试次数和 Token 用量 |
| 响应式工作台 | 包含首页、候选人列表与详情、岗位列表与详情、调用监控页面，适配桌面与手机 |
| 测试与评估 | 提供 pytest 测试，以及包含 12 组候选人—岗位样例的人工标注评估集 |

### 界面设计

当前前端采用深色侧边导航、浅色内容区和青绿色主题，统一了卡片、表格、上传区域、空状态和弹窗的视觉样式。手机端使用四项导航布局，详情和操作区域会随屏幕宽度调整。

界面文案目前为英文，本 README 为中文。前端改版保留了原有上传、解析、匹配、评分及面试题生成流程。

## 使用流程

1. 打开 **Candidates**，粘贴简历文本或上传文件，生成候选人档案。
2. 打开 **Jobs**，录入职位描述，提取必备技能、加分技能和最低经验要求。
3. 进入岗位详情，查看排序后的候选人；也可以从候选人详情查看匹配岗位。
4. 点击 **Score** 查看匹配评分与解释，点击 **Interview Qs** 生成面试问题。
5. 在 **Observability** 查看模型调用和 Token 使用情况。

评分与生成内容用于辅助人工审阅，不应直接作为录用或淘汰结论。

## 技术架构

```mermaid
flowchart TB
    User[招聘人员] --> UI[Next.js 招聘工作台]
    UI --> API[FastAPI 接口]
    API --> Services[解析、检索、评分与面试服务]
    Services --> Parser[Pydantic 结构化校验与修复重试]
    Parser --> LLM[OpenRouter 大语言模型]
    Services --> Embedding[本地 sentence-transformers 向量模型]
    Services --> Search[向量召回与规则重排]
    Embedding --> DB[(PostgreSQL + pgvector)]
    Search --> DB
    Services --> DB
    Services --> Logs[审计记录与模型调用日志]
    Logs --> DB

    classDef ui fill:#e3eeeb,stroke:#087f75,color:#182c35
    classDef service fill:#eaf0fa,stroke:#557db4,color:#182c35
    classDef data fill:#faf1df,stroke:#a57b32,color:#182c35
    class User,UI ui
    class API,Services,Parser,LLM,Embedding,Search service
    class DB,Logs data
```

| 层级 | 技术与用途 |
| --- | --- |
| 前端 | Next.js 16、React、TypeScript、App Router |
| 界面组件 | Tailwind CSS、shadcn/ui、Base UI、Lucide 图标 |
| 后端 | Python 3.12、FastAPI、Uvicorn |
| 数据存储 | PostgreSQL 16、pgvector、SQLAlchemy |
| 数据校验 | Pydantic、pydantic-settings |
| 大语言模型 | 通过 OpenRouter 调用模型，负责解析、评分和面试题生成 |
| 向量模型 | 本地运行 `all-MiniLM-L6-v2`，输出 384 维向量 |
| 测试 | pytest、FastAPI TestClient、Faker |
| 运行环境 | Docker Compose，包含数据库、后端和前端三个服务 |

### 检索排序与模型评分

这两类结果采用不同的计算方式：

- **检索重排分数**：先通过 pgvector 余弦距离召回最多 20 条记录，再按向量相似度 50%、技能重合度 30%、经验匹配度 20% 加权排序，默认返回前 10 条。
- **模型匹配评分**：用户点击 Score 后，将候选人与岗位的结构化信息交给大语言模型，生成 0–100 分及文字解释。

经验项按候选人年限占岗位最低要求的比例计分，达到或超过要求即得满分。岗位没有最低年限要求时，经验项也计满分。技能重合度使用忽略大小写的精确匹配，尚未做技能别名归一化。

### 模型输出处理

结构化输出会经过 JSON 解析与字段校验；失败时，将校验错误反馈给模型，最多尝试 3 次。对于上游 `429`、`502`、`503`、`504` 响应，客户端提供等待重试，持续不可用时由接口返回 `503`。

模型调用耗时取决于所选模型和上游负载，部分调用可能需要数十秒。

## 本地启动

### 1. 准备环境

- 安装 Docker 和 Docker Compose；Windows 可使用已启动的 Docker Desktop。
- 准备 OpenRouter API Key，用于真实的简历解析、岗位解析、评分和面试题生成。
- 确认本机 `3000`、`8000`、`5432` 端口可用。

以下 Docker 命令均在项目根目录执行，可直接用于 PowerShell 或常见终端。使用 Docker 启动时，本机不需要额外安装 Node.js 和 Python。

### 2. 配置后端环境变量

在 `backend` 目录创建 `.env` 文件；如果已经存在，请编辑原文件，保留现有配置。最小示例：

```dotenv
APP_ENV=development
OPENROUTER_API_KEY=替换为你的_API_Key
LLM_PROVIDER=openrouter
LLM_MODEL=openai/gpt-oss-20b:free
EMBEDDING_MODE=local
CORS_ORIGINS=http://localhost:3000
```

`LLM_MODEL` 是当前代码中的默认模型标识，实际使用时需确认自己的 OpenRouter 账户可调用该模型，也可以替换为可用模型。是否收费取决于所选模型，不应将示例配置视为永久免费承诺。

Docker Compose 会为后端注入容器内的 `DATABASE_URL`，连接名为 `postgres` 的数据库服务。API Key 仅放在后端配置中，不要写入前端或提交到仓库。

### 3. 首次初始化数据库

启动数据库并构建后端镜像：

```sh
docker compose up -d --wait postgres
docker compose build backend
```

首次使用空数据库时，启用向量扩展并创建数据表：

```sh
docker compose exec -T postgres psql -U postgres -d recruitment_copilot -c "CREATE EXTENSION IF NOT EXISTS vector;"
docker compose run --rm --no-deps backend python -c "from app.db import Base, engine; import app.models; Base.metadata.create_all(engine)"
```

目前仓库包含 Alembic 配置，但没有版本迁移脚本；应用启动时也不会自动建表。上述命令用于创建缺失的表，不会清空已有数据，也不会自动迁移已有表的结构。

### 4. 启动完整应用

```sh
docker compose up -d --build
docker compose ps
```

| 地址 | 用途 |
| --- | --- |
| [http://localhost:3000](http://localhost:3000) | 招聘工作台 |
| [http://localhost:8000/docs](http://localhost:8000/docs) | 交互式 API 文档 |
| [http://localhost:8000/health](http://localhost:8000/health) | 后端进程健康接口 |

`/health` 仅返回后端进程的响应状态，不验证数据库连接或模型服务是否可用。

首次使用本地向量模型时可能需要下载模型文件，请确保容器可以访问模型下载源。

### 5. 可选：导入演示数据

```sh
docker compose run --rm backend python -m seed.seed_data
```

每次执行会追加 15 位模拟候选人和 8 个模拟岗位。脚本直接生成结构化数据，不调用大语言模型；生成检索向量时仍使用配置的向量模型。请避免不必要的重复导入。

## 开发与常用操作

### 前端本地开发

需要本机安装 Node.js 22 和 npm。先确保数据库、后端已经启动，并停止占用 `3000` 端口的前端容器：

```sh
docker compose stop frontend
cd frontend
npm ci
npm run dev
```

本地前端默认请求 `http://localhost:8000`。如需修改，在 `frontend/.env.local` 中设置 `NEXT_PUBLIC_API_URL`，然后重启开发服务。

### 更新 Docker 中的前端

修改源码后，仅点击 Docker Desktop 的 Start 不会重新构建镜像。请回到项目根目录执行：

```sh
docker compose up -d --build --no-deps frontend
```

如果之前运行了本地 `npm run dev` 或其他前端预览，先在对应终端按 `Ctrl+C` 停止进程，释放 `3000` 端口。

Docker 中的 `NEXT_PUBLIC_API_URL` 通过 `docker-compose.yml` 的构建参数设置。修改后需要重新构建前端镜像。

### 查看状态与日志

```sh
docker compose ps -a
docker compose logs --tail 100 frontend
docker compose logs --tail 100 backend
```

停止服务可执行 `docker compose stop`，再次启动已有容器可执行 `docker compose start`。

## 测试与评估

### 前端检查

在 `frontend` 目录执行：

```sh
npm run lint
npm run build
```

### 后端自动化测试

测试会清空目标数据库中的业务表，必须使用独立测试库。仅设置 `APP_ENV=test` 不会自动替换数据库地址。

在项目根目录创建测试库；已存在时无需重复创建：

```sh
docker compose exec -T postgres psql -U postgres -c "CREATE DATABASE recruitment_copilot_test;"
```

然后显式指定测试库：

```sh
docker compose run --rm -e DATABASE_URL=postgresql+psycopg://postgres:postgres@postgres:5432/recruitment_copilot_test -e APP_ENV=test backend pytest -v
```

测试中的模型调用使用模拟实现，向量使用确定性测试实现；接口测试仍需要实际运行的 PostgreSQL 和 pgvector。

### 模型效果评估

```sh
docker compose run --rm backend python -m eval.run_eval
```

评估脚本使用 12 组人工标注样例，检查生成评分是否落入预期的强匹配、中等匹配或弱匹配区间。该脚本会调用真实模型，需要网络和有效的 API Key，可能产生费用，不属于自动化单元测试。小规模样例的结果不代表真实招聘场景下的准确率。

## 主要 API

| 方法与路径 | 用途 |
| --- | --- |
| `GET /candidates`、`GET /candidates/{id}` | 获取候选人列表与详情 |
| `POST /candidates`、`POST /candidates/upload` | 从文本或文件创建候选人 |
| `GET /jobs`、`GET /jobs/{id}` | 获取岗位列表与详情 |
| `POST /jobs`、`POST /jobs/upload` | 从文本或文件创建岗位 |
| `GET /search/jobs/{job_id}/candidates` | 检索岗位对应的候选人 |
| `GET /search/candidates/{candidate_id}/jobs` | 检索候选人对应的岗位 |
| `POST /scoring/{candidate_id}/{job_id}` | 生成并保存匹配评分 |
| `GET /scoring/{candidate_id}/{job_id}` | 获取已有评分记录 |
| `POST /scoring/{candidate_id}/{job_id}/evidence` | 按岗位必备要求查找并核验简历原文 |
| `POST /interviews/{candidate_id}/{job_id}/questions` | 生成面试问题 |
| `GET /observability/stats` | 获取模型调用统计 |
| `GET /health` | 检查后端进程响应 |

具体请求字段与响应结构请查看启动后的 [API 文档](http://localhost:8000/docs)。

## 目录结构

```text
AI Recruitment Copilot/
├── backend/
│   ├── app/                 # API 路由、业务服务、数据模型与校验结构
│   ├── tests/               # 单元测试与接口测试
│   ├── eval/                # 人工标注样例与模型效果评估
│   ├── seed/                # 演示数据生成
│   └── alembic/             # 数据库迁移配置，尚无版本脚本
├── frontend/
│   ├── app/                 # 页面、布局和全局样式
│   ├── components/          # 导航、页头和 UI 组件
│   ├── lib/                 # API 客户端与工具函数
│   └── public/              # 静态资源
├── docs/                    # 架构、演示及成本说明
├── scripts/                 # 辅助配置脚本
├── docker-compose.yml       # 本地容器编排
└── README.md
```

## 当前限制与后续方向

- PDF 输入目前依赖文本提取，未集成 OCR；扫描件可能无法解析。
- 尚未提供登录、角色权限、批量导入、招聘流程看板或解析结果编辑。
- 语音面试仍为计划功能，当前仅生成文字面试问题。
- 技能别名识别和更充分的评估数据仍待完善。
- 后续可在建立检索相关性标注集后，评估是否引入交叉编码器重排模型。

## 相关文档

- [系统架构说明](docs/architecture.md)
- [成本、可靠性与安全说明](docs/cost-safety-notes.md)
- [演示脚本](docs/demo-script.md)
