# tryon_service · 虚拟试穿 sidecar

衣溯AI 的虚拟试穿模块，从独立仓库并入本平台。形态是**同仓不同进程**：本目录用自己的 Python 3.10 venv 起
uvicorn（默认 `127.0.0.1:8000`），与平台主服务 `backend/`（Python 3.14、`:8765`）互不干扰，因此模块内
148 处 `from app.` import 一个字都没改。

完整文档在 `docs/`：

| 文件 | 内容 |
| --- | --- |
| `docs/README.md` | 快速开始 / 配置项 / 接口一览 / 算法降级矩阵 / 常见问题 / 并入形态说明 |
| `docs/PROJECT_DOC.md` | 项目书正文：流程图、方案对比、实测数据、局限性、公网部署 |
| `docs/MERGE_PLAN.md` | 并入平台的分阶段计划与逐阶段验收账（P1–P5，含 commit 号与回滚方式） |

## 一分钟跑起来（Windows）

```powershell
cd tryon_service
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
# 另开终端跑平台前端（vite 已配好 /api/v1、/tryon-assets、/tryon-results 三条代理）
cd ..\frontend ; npm run dev
```

浏览器打开 `http://127.0.0.1:5173/museum/tryon`。首页 3D 博物馆点展品「试穿此服饰」会带
`?garment=<素材 slug>` 深链过来，命中素材库就自动选中。

## 与平台的三条接缝

1. **数据库**：`tryon_garments` / `tryon_records` 两张表直接建在平台主库里（本机
   `backend/data/yisu_prod.db`，生产同一个 MySQL 库）。列定义的唯一事实源是
   `database/tryon_schema.sql`，`tests/test_db_contract.py` 会同时校验本模块的 async ORM 与平台
   `backend/app/db/models.py` 的 sync ORM，防止两边漂移。
2. **前端**：模块页面在 `frontend/src/tryon/`，路由 `/museum/tryon{,/gallery,/history}`，
   由 `TryonLayout.vue` 提供模块子导航与后端健康标签。样式只用 `--yisu-*` 变量，不覆盖平台的 `--el-*`。
3. **静态资源**：只挂三类只读资产 —— `/tryon-assets/garments`、`/tryon-assets/samples`、
   `/tryon-results`。生产把 `YISU_RESULTS_ROOT` 指到 `backend/uploads/tryon` 并把
   `YISU_RESULTS_URL_PREFIX` 改成 `/uploads/tryon`，结果图就直接复用平台 nginx 既有的 `/uploads/` 规则。

## 配置

见 `.env.example`。三个容易踩的默认值：

- `YISU_DATABASE_URL=` 留空 → 自动复用平台 SQLite 主库；生产填 `mysql+aiomysql://…`（异步驱动，
  与平台侧同步 ORM 的 `pymysql` 互不影响，驱动装在 `requirements-mysql.txt`）。
- `YISU_SQLITE_WAL=false` → 默认不开 WAL。WAL 是写进库文件的持久设置，还会产生 `-wal/-shm` 旁文件，
  而平台有按单文件拷贝库的习惯。
- `YISU_RESULTS_ROOT` 与 `YISU_RESULTS_URL_PREFIX` 必须成对修改，只改一个会得出「图能存下来但访问不到」
  的形态；启动日志检测到这种组合会直接告警。

## 生产装配件

- `../yisu-tryon.service`：systemd unit。单 worker 是有意的（MediaPipe 模型与线程池在进程内），
  `CPUQuota=200%` 防止 TPS 把平台主服务和 MySQL 挤垮。
- `../yisu_nginx.conf`：`/api/v1/` 反代到 8000 并按 IP 限流（TPS 单请求吃满 1–2 核，限流是必须项），
  `/tryon-assets/` 长缓存。

## 自检

```powershell
.\.venv\Scripts\python.exe -m pytest -q                 # 54 passed
.\.venv\Scripts\python.exe -m scripts.doctor --selftest # 端到端出图 + 依赖体检
```

跑任何一侧重考前先 `$env:PYTHONPATH=""`：平台的 `backend/app` 没有 `__init__.py`（命名空间包），
环境变量串门会让进程 import 到另一侧的 `app`，而平台 venv 缺 `greenlet`，会直接报错。

## 已知边界

本服务没有鉴权，`/api/v1/history` 返回全局列表；结果目录里存着 `person_source.jpg`（历史页要做原图
对比），所以拿到他人 `task_id` 仍能看到那张人像。多租户对外开放前必须加访问控制或签名 URL，并补
「删除我的记录」接口。
