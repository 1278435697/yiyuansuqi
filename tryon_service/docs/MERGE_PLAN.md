> 本文件是虚拟试穿模块的原始文档（写于独立仓时期）。并入平台后的路径对照：
> `backend/` → `tryon_service/`，`frontend/` → `frontend/src/tryon/`（平台 SPA）。
> 运行与部署的权威说明见上级目录 `README.md`，以及平台根 `README.md` 的「模块 10 · 虚拟试穿」章节。

# 虚拟试穿模块 → yisu-ai-platform 合并方案

> 状态：**已执行完成（P1–P5）**——逐阶段验收账与遗留项见第 7 节
> 形态决策（已确认）：**同仓 + sidecar 独立服务**，数据库**并入平台 SQLAlchemy Base**
> 基线：`D:\yisu-ai-platform` 已 `git init` 并完成 pre-merge 基线提交 `e09964a`（534 个文件，`.env`/`uploads`/`*.db`/`node_modules`/`.venv` 均已 ignore）
> 回滚锚点：`git tag pre-tryon-merge` 已打上，指向 `e09964a`

---

## 0. 结论

能合，而且平台的坑位本来就是给这个模块留的：

| 证据 | 位置 |
| --- | --- |
| 平台后端**零**试穿代码 | `backend/app/api/` 14 个 router 全无 tryon/try_on |
| 前端坑位已注册 | `frontend/src/router/index.ts:19` → `/museum/tryon` → `TryonPlaceholder.vue`，页面原文写着「正式接入 2D/3D 试穿模块后，此处将渲染该服饰的上身效果」 |
| 展品联动已写好 | `MuseumView.vue` 的 `goTryon()` + `exhibits.json` 4 件展品带 `tryonId`，命名与我们的素材 slug 同源（`quju-shenyi` 完全一致） |
| 技术栈同源 | 两边都是 Vue 3.5 + Element Plus + Pinia + Axios + vue-tsc；后端都是 FastAPI + pydantic-settings + SQLAlchemy 2 |

sidecar 形态带来一个决定性的好处：**模块可以整体原样搬，148 行 `from app.` import 一行都不用改**（两个服务各有独立 venv 与独立 source root，同名 `app` 包不会冲突）。真正需要动手术的地方一共 8 处，全部列在下面。

---

## 1. 合并后的目录结构

```
D:\yisu-ai-platform\
├─ backend\                      平台主服务（8765，py3.14 venv）——仅 3 处侵入
│  ├─ app\db\models.py           + TryonGarment / TryonRecord 两个模型
│  ├─ app\main.py                不动（不挂试穿 router）
│  └─ uploads\tryon\{task_id}\   试穿运行时产物（sidecar 写、平台 mount 读）
├─ tryon_service\                ← 本工作区 backend\ 整体迁入（8000，py3.10 venv）
│  ├─ app\                       45 个 py 文件原样，import 不改
│  ├─ scripts\  tests\  requirements-core/-ai/-dev/-gpu.txt
│  ├─ data\garments\  data\samples\          版本管理的素材资产（6.0 MB，入库）
│  ├─ data\{results,uploads,logs,cache}\     运行时产物（gitignore）
│  └─ .env.example → .env
├─ database\
│  └─ tryon_schema.sql           ← 两张表的**唯一事实源**，两边各自执行/校验
├─ frontend\                     唯一前端（我们的 22 个 src 文件并入）
├─ yisu_nginx.conf               +2 个 location
└─ yisu-tryon.service            新增（参照 yisu-backend.service）
```

**为什么运行时产物写进 `backend/uploads/tryon/` 而不是自己的 `data/results/`**
平台 nginx 已有 `location /uploads/ { alias .../backend/uploads/; }`，产物放进去就自动可访问、自动纳入服务器既有磁盘清理与备份策略，**生产零 nginx 改动**；而素材图（repo 资产，需入库）走独立 mount，不与用户数据混淆。

---

## 2. 分阶段执行清单

### P1 目录与素材落位（0.5 h，零风险）
1. `git tag pre-tryon-merge`
2. 拷贝本工作区 `backend\` → `D:\yisu-ai-platform\tryon_service\`，**排除** `.venv`、`data\results`、`data\e2e`、`data\garments_src`（11.7 MB 原图，只留 `garments\` 里 20 个已产出文件 + `samples\` 2 个）、`__pycache__`、`logs`
3. 拷贝本工作区 `.gitignore` 中试穿相关规则，追加到平台 `.gitignore`：
   ```
   tryon_service/.venv/
   tryon_service/data/results/
   tryon_service/data/uploads/
   tryon_service/data/logs/
   tryon_service/data/cache/
   tryon_service/data/e2e/
   tryon_service/data/garments_src/
   tryon_service/weights/
   ```
4. 在 `tryon_service\` 里建 py3.10 venv 并装 `requirements-core.txt` + `-ai.txt`（本机已有可用的 3.10 环境，直接复用其解释器路径建 venv 最省时间）
5. `cd tryon_service ; pytest -q` → **应 44 passed**（此阶段与平台完全无关，绿了就说明搬运无损）
6. 提交 `feat(tryon): 迁入虚拟试穿服务为独立 sidecar`

### P2 数据库并入（1.5 h）
1. 新建 `database\tryon_schema.sql`，两张表 DDL（MySQL 8 / SQLite 双兼容）：
   - `tryon_garments`：`id VARCHAR(64) PK`、`name/dynasty/category`、`tags JSON`、`image_path/mask_path/thumb_path`、`keypoints JSON`、`bbox_area_ratio FLOAT`、`source_text TEXT`、`references JSON`、`costume_id INT NULL`（预留 → `costumes.id`）、`created_at DATETIME`
   - `tryon_records`：`id INT AI PK`、`task_id VARCHAR(64) INDEX`、`garment_id VARCHAR(64) FK→tryon_garments.id ON DELETE SET NULL`、`user_id INT NULL FK→users.id`、`person_url/result_url/mask_url/pose_url/warp_url`、`backend_used/quality/status`、`warnings JSON`、`timings JSON`、`created_at DATETIME INDEX`
   - **表名改成带前缀的复数**（原 `garment` / `tryon_record`）：平台表全是复数（`costumes`/`users`/`likes`/`collections`），单数 `garment` 既不一致也容易和 `costumes` 混
2. `backend\app\db\models.py` 追加 `TryonGarment` / `TryonRecord`（**平台同步风格**：`Column` + `declarative_base` 的 `Base`，与现有 22 个类一致，不引入 `Mapped[]`）
3. `tryon_service\app\db\models.py` 改 `__tablename__` 为新表名 + 补 `user_id`/`costume_id` 两列（sidecar 保留自己的一份定义，**不 import 平台 models**：跨 venv 的包耦合比"两份列定义需同步"更糟，一致性由下面的契约测试兜）
4. `tryon_service\app\db\base.py`：`create_async_engine` 增加 SQLite 多进程并发保护 —— `connect_args={"timeout": 15}` + `event.listens_for(engine.sync_engine, "connect")` 里 `PRAGMA journal_mode=WAL; PRAGMA busy_timeout=5000;`（本地 sidecar 与平台进程共用 `yisu_prod.db` 时必须；生产走 MySQL 无此问题）
5. `tryon_service\app\services\seed.py` 的 upsert 与 `scripts\seed_garments.py` 跟随表名改动
6. **契约测试**（新增，放 `tryon_service\tests\db_contract.py`）：读取 `database\tryon_schema.sql` 解析出列名集合，断言与 sidecar 模型 `__table__.columns` 完全一致 → 两边漂移立刻炸测试
7. `tryon_service` 的 `.env` 指向平台库：
   - 生产/服务器：`YISU_DATABASE_URL=mysql+pymysql://…`（需给 sidecar venv 补 `pymysql`）
   - 本机（**当前无 MySQL，见第 4 节决策点 A**）：`YISU_DATABASE_URL=sqlite+aiosqlite:///../backend/data/yisu_prod.db`，同时平台 `backend\.env` 需 `USE_SQLITE_PROD=true`
8. 提交 `feat(db): 试穿两张表并入平台 schema（单一事实源 tryon_schema.sql）`

### P3 前端入口打通（1 h）
1. 文件搬迁映射（全部加 `tryon` 命名前缀，避免和平台同名文件混淆）：

   | 源（本工作区 `frontend\src\`） | 目标（平台 `frontend\src\`） |
   | --- | --- |
   | `views\TryOnView.vue` | `views\tryon\TryOnIndex.vue` |
   | `views\GalleryView.vue` / `HistoryView.vue` | `views\tryon\Gallery.vue` / `History.vue` |
   | `views\NotFound.vue` | **不搬**（平台已有 404 语义） |
   | `components\{ImageUploader,GarmentPicker,PipelineStepper,ResultViewer,TraceCard}.vue` | `components\tryon\…` |
   | `store\tryon.ts` | `store\tryon.ts`（平台无同名） |
   | `store\app.ts` | `store\tryonMeta.ts`（平台 `store/user.ts` 已有全局态，避免两个 `app` store） |
   | `api\{client,tryon,garments,health}.ts` | `api\tryonClient.ts` / `tryon.ts` / `tryonGarments.ts` / `tryonHealth.ts` |
   | `types\index.ts` | `types\tryon.ts` |
   | `utils\{compressImage,guards,snapshot}.ts` | `utils\tryon\…` |
2. `api\tryonClient.ts` 的 baseURL 改成与平台 `request.ts` 同构：
   `import.meta.env.DEV ? "http://127.0.0.1:8000/api/v1" : "/api/v1"`，**保留自己的 120 s 超时 / 重试 / AbortSignal**（不并入平台 `request.ts`：它 30 s 超时会掐断 HD 推理，且它的拦截器按 `detail` 取错误文案）
3. 路由：`/museum/tryon` 的 component 从 `TryonPlaceholder.vue` 换成 `views/tryon/TryOnIndex.vue`（保留 `meta.bareLayout: true`），另加 `/tryon`（普通布局，带平台导航）、`/tryon/gallery`、`/tryon/history`
4. `TryOnIndex.vue` 支持展品深链：`onMounted` 读 `route.query.garment` → 命中则自动选中该素材；`route.query.from === 'museum'` 时显示「返回展厅」
5. `App.vue` 导航在「博物馆」后插入 `<router-link to="/tryon">虚拟试穿</router-link>`
6. `vite.config.ts` proxy 增加 `/uploads` → `http://127.0.0.1:8765`（平台已 mount `/uploads`，与 sidecar 写入的是同一物理目录），这样**结果图在 dev/prod 都用相对路径**，前端零特判
7. `package.json` 依赖只加一条：`@element-plus/icons-vue ^2.3.1`（平台没有，我们的组件用了图标）；**其余版本一律沿用平台**（vite 5.4 / element-plus 2.8 / TS 5.6），不做升级
8. 素材 id 对齐：`exhibits.json` 的 `yuanlingpao-tang` → `yuanling-pao`、`beizi-song` → `beizi`；`aoqun-ming` 见第 4 节决策点 B
9. 提交 `feat(frontend): 虚拟试穿并入（替换占位页 + 导航/路由/素材联动）`

### P4 服务端装配与部署（0.5 h）
1. **URL 前缀切换**（sidecar 内 3 个文件）：
   - `app\config.py`：新增 `asset_prefix: str = "/tryon-assets"`；`results_dir` 改为 `Path("../backend/uploads/tryon").resolve()`
   - `app\main.py`：`app.mount(settings.asset_prefix, StaticFiles(directory=settings.data_dir))`（替掉 `/static`）
   - `app\utils\static.py`：生成的 URL 前缀 —— 素材/中间产物用 `/tryon-assets/...`，结果与上传副本用 `/uploads/tryon/...`
   - 影响面：`schemas` 的 `*_url` 字段值、`history` 落库值、`ImageUploader.vue` 的 `SAMPLE_PERSONS` fetch 路径、4 处测试断言（`result_url.startswith("/static/results/")` → `"/uploads/tryon/"`）
2. 错误体加 `detail`：`app\errors.py` 的响应模型里加 `detail = message` 的别名赋值 → 平台前端的拦截器（读 `data.detail`）与我们前端的拦截器（读 `message`）**同时满足**
3. `requirements-core.txt` 补 `pymysql>=1.1`（sidecar 连 MySQL 用）；`YISU_CORS_ORIGINS` 默认已含 `http://localhost:5173`，无需改
4. `yisu_nginx.conf` 追加（`/uploads/` 与 `client_max_body_size 20m` 复用现有）：
   ```nginx
   location /api/v1/ {
       proxy_pass http://127.0.0.1:8000/api/v1/;
       limit_req zone=tryon burst=3 nodelay;   # CPU 推理防刷
       proxy_read_timeout 180s;
   }
   location /tryon-assets/ {
       alias /www/wwwroot/yisu/tryon_service/data/;
       expires 7d;
   }
   ```
   并在 `http` 块加 `limit_req_zone $binary_remote_addr zone=tryon:10m rate=6r/m;`
5. `yisu-tryon.service`：照 `yisu-backend.service` 改 `WorkingDirectory=/www/wwwroot/yisu/tryon_service`、`ExecStart=/www/wwwroot/yisu/tryon_service/.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`
6. 本机开发脚本：把 `scripts\dev-start.ps1` / `dev-stop.ps1` 复制进 `tryon_service\scripts\`，端口/路径参数化，并在平台 README 里加「三进程启动顺序：tryon(8000) → backend(8765) → frontend(5173)」
7. 提交 `chore(deploy): sidecar systemd + nginx 路由与限流`

### P5 端到端验证与文档（0.5 h）
1. `tryon_service`：`pytest -q`（应 ≥45 passed）；`scripts\doctor.py --selftest`
2. 平台：`backend\.venv` 起 8765（本地需决策点 A 落定），`/health` 200，且 `from app.db.models import TryonGarment, TryonRecord` 可导入
3. 前端：`npm run typecheck` 0 error、`npm run build` 成功、dist 内出现 tryon chunk
4. 浏览器链路：`/museum` 点展品「试穿此服饰」→ 自动选中素材 → 出图 → 结果图 src 是 `/uploads/tryon/…` 且能渲染 → 再点一次出现「结果与上次完全相同（命中磁盘缓存）」黄条 → 勾选「跳过缓存强制重算」换新 task → `/tryon/history` 有记录
5. 回归：平台原 9 个页面 + 博物馆 + 面料 + 社区 console 0 error
6. 文档：平台 `README.md` 加「模块 10 · 虚拟试穿」一节；本工作区 `README.md`/`PROJECT_DOC.md` 移到 `tryon_service\` 下并在平台 README 里指路

---

## 3. 侵入式改动总账（一共 8 处，都可单独 revert）

| # | 平台文件 | 改动 |
| --- | --- | --- |
| 1 | `backend\app\db\models.py` | +2 个模型类（追加，不改现有类） |
| 2 | `database\tryon_schema.sql` | 新文件 |
| 3 | `frontend\src\router\index.ts` | 1 行 component 替换 + 3 条新路由 |
| 4 | `frontend\src\App.vue` | 1 行 nav |
| 5 | `frontend\vite.config.ts` | +1 个 `/uploads` proxy |
| 6 | `frontend\package.json` | +1 个 dep |
| 7 | `frontend\src\data\exhibits.json` | 2 处 tryonId 对齐 |
| 8 | `yisu_nginx.conf` + 新 `.service` | +2 location / +1 unit |

不改的：平台 `main.py`、任何现有 router/service/ai_engine、`core\config.py`、`db\database.py`、平台 venv 的依赖版本。

---

## 4. 需要你先定的 3 个点

**A. 本地根本没有 MySQL。** 实测 `127.0.0.1:3306 CLOSED`、`8765 未监听`，而平台 `.env` 是 `USE_DEMO_DATA=false` + `USE_SQLITE_PROD=false` → **平台后端目前在本机起不来**（`lifespan` 里 `init_prod_db()` 会抛并 raise）。但 `backend\data\yisu_prod.db` 是存在的，说明以前是用 SQLite 正式库跑过的。
→ 建议：本机把 `USE_SQLITE_PROD=true` 打开，sidecar 的 `YISU_DATABASE_URL` 指同一个 `yisu_prod.db`（WAL + busy_timeout 已列入 P2 第 4 条）；生产仍走 MySQL。要不要我动 `backend\.env`（它是 gitignored 的你的本地文件）？

**B. `aoqun-ming`（明制袄裙）我们没有素材。** 现有 6 件是 `quju-shenyi / qixiong-ruqun / yuanling-pao / beizi / mamian-qun / tang-banbi`。
→ 推荐：用现成的 ImageGen + `register_garments.py` 流水线补一件明制袄裙（约 20 分钟，含肉眼验收），exhibits.json 的 id 不动；备选：把该展品 tryonId 先指向 `mamian-qun` 并在 json 里注释说明。

**C. 行尾。** git 提交时刷屏 `LF will be replaced by CRLF`，说明有 autocrlf 介入。合并过程我不会碰 `git config`；如果你希望 diff 干净，需要你自己执行 `git config core.autocrlf false`（建议但非必须）。

---

## 5. 已知风险（如实）

1. **平台前端与我们的前端样式体系不同**：平台是 Tailwind + 自绘「绢金/墨红」主题 CSS 变量（`--silk-gold` 等），我们的组件是 Element Plus 默认样式 + scoped CSS。合并后视觉会「两套味」。P3 只保证功能可用；配色统一建议单独一轮（把我们的 `scoped` 色值改用平台 CSS 变量）。
2. **依赖版本降级风险**：我们的组件在 element-plus 2.8 / vite 5.4 上没跑过，`el-alert`/`el-switch`/`el-steps` 用法都是老 API，预计 0 改动，但以 `vue-tsc --noEmit` + 实跑为准。
3. **生产环境的分割链路**：服务器若是 Python 3.14（与平台 venv 同源），`mediapipe` 无对应 wheel → 自动降级 GrabCut 启发式，实测观感明显掉档。sidecar 用**独立 3.10/3.12 venv** 正是为规避这一点；万一服务器装不了 3.10，退路是 `scripts\download_weights --asset u2netp`（4 MB）+ `onnxruntime`，走已实现的 U2Net Provider，画质优于启发式。
4. **CPU 推理是共享资源**：TPS 单请求 2–3 s 吃满 1–2 核，与平台主服务同机时 P4 的 nginx `limit_req` 是**必须项**，不是可选优化。
5. **真人照片合规**：产物落在 `backend\uploads\tryon\`，与平台 uploads 同生命周期；`PROJECT_DOC.md` 局限性第 7 条已经声明「无删除接口」，合并上线公网前需要补 `DELETE /api/v1/history/{task_id}`（可作为 P6）。
6. **`user_costume_log` 联动**：平台已有 `action_type` 枚举（`view/search/draft/like/post`），加 `tryon` 即可让试穿进个性化推荐数据源 —— 属于收益明显但非必需的 P6 项。

---

## 6. 工作量预估

| 阶段 | 时间 | 交付判据 |
| --- | --- | --- |
| P1 目录与素材落位 | 0.5 h | sidecar 独立 44 passed |
| P2 数据库并入 | 1.5 h | 契约测试绿 + 两进程同读写一库不报锁 |
| P3 前端并入 | 1 h | typecheck 0 error + 展品深链出图 |
| P4 服务端装配与部署 | 0.5 h | URL 前缀切换 + 45 passed |
| P5 端到端与文档 | 0.5 h | 第 2 节 P5 清单全绿 |
| **合计** | **约 4 h** | |

建议按 P1→P5 顺序执行，每阶段独立提交；**P1 结束就已经得到一个「搬进平台仓库但完全独立可跑」的安全中间态**，后面任何一步失败都不影响这个态。

---

## 7. 执行账（P1–P5 已完成）

### 7.1 提交链

```
e09964a (tag pre-tryon-merge)  合并前基线
25aede9  P1  sidecar 迁入 tryon_service/（87 文件）
5c72aea  P2  两张表并入平台主库 + schema 契约（6 文件）
c331444  同期并行工作：纹样资料库（你自己的改动，按要求单独成一个 commit）
add4a5b  P3  前端并入 frontend/src/tryon（28 文件）
e60edfc  P4  静态面拆分 + 部署装配
```

### 7.2 逐阶段验收

| 阶段 | 判据 | 实测 |
| --- | --- | --- |
| P1 | sidecar 独立可跑 | `pytest -q` 44 passed；建 venv + 拷贝 `data/` 无损 |
| P2 | 契约绿 + 两进程同读写一库不报锁 | 平台库建表前后快照：`journal_mode=delete` 不变、表数 20→22、`added=['tryon_garments','tryon_records']`、`lost=[]`、已有表行数无变化；平台 py3.14 venv 反射对比列集合 14/14 与 15/15；`seed_garments` 写入 6 条可在平台侧读出 |
| P3 | typecheck 0 error + 展品深链出图 | `vue-tsc --noEmit` exit 0；`vite build` exit 0 且产出 `TryonLayout`/`TryOnView` chunk；两轮浏览器复验（第一轮发现 `vite.config.js` 遮蔽与 `bareLayout` 裁切两个真问题并根治） |
| P4 | URL 前缀切换 + 测试全绿 | `/tryon-assets/garments/beizi_thumb.png` 200、`/static/**` 404、新跑一次 `result_url=/tryon-results/<task>/result.jpg` 200；旧记录里的 `/static/results/` 在读取层改写后 200；`pytest -q` 54 passed（两侧一致） |
| P5 | 第 2 节清单 | `tryon_service` pytest 54 passed；`doctor --selftest` 通过（端到端出图，total 4.22s）；平台 venv `from app.db.models import TryonGarment, TryonRecord` 可导入；typecheck/build 再次 exit 0；浏览器链路全绿（详见 7.3）；文档已进 `tryon_service/docs/` + 平台 README 「模块 10」章节 |

### 7.3 P5 浏览器端到端实测（经平台 vite :5173）

- `/museum/tryon`：平台顶部导航在、可滚动（`documentElement.scrollHeight` 2562 vs `innerHeight` 948）；健康标签「试穿服务正常 · TPS 几何兜底」；6 张缩略图 `currentSrc` 均为 `/tryon-assets/garments/*_thumb.png` 且 `naturalWidth>0`。
- `?garment=beizi` 深链：弹「已选中展厅带来的「对襟褙子」」且仅该卡 `is-active`；未知 slug 弹 warning，无卡片激活。
- 真实推理：`POST /api/v1/tryon` 200 / 2046 ms（缓存命中 289 ms 时会可见提示，不静默）；结果图 `/tryon-results/be13077d7ba34fb2/result.jpg` 200 / 683 px；7 条降级告警全部可见；溯源卡正常。
- `/museum/tryon/history`：4 条记录 result/origin 全 200，页面里 `/static/results/` 出现次数 = 0。
- 回归：`/museum` 3D canvas WebGL 存活、60 FPS、无 4xx/5xx；`/museum/tryon/gallery` 6 件素材正常。
- 唯一异常（不属于合并回归）：首页 `/` 硬连平台主后端 `127.0.0.1:8765` 被拒 —— 本机 MySQL/8765 未启动，与 sidecar 链路无关（即第 4 节 A 点未落定的现有表现）。

### 7.4 执行中改过的计划项

- **静态面比计划更窄**：计划只要求拆前缀；实施时额外把 `data/uploads` 从对外面拉回来（旧的整目录 `/static` 把上传原图一并公开了），并在历史/缓存读取层改写库内旧 URL。残留风险见 `README.md` 第十二节：结果目录里仍有 `person_source.jpg`，本服务无鉴权。
- **`errors` 加 `detail` 别名**（计划外）：平台 axios 拦截器只读 `data.detail`，模块只读 `message`，两套前端共用一个 sidecar 时两边都不能断。
- **前端并入额外修了两个平台坑**：`vue-tsc -b` 生成的陈旧 `vite.config.js` 遮蔽 `.ts`（已在 `tsconfig.node.json` 设 `outDir` 根治）；`meta.bareLayout` 会把长页裁死（三条试穿路由改用平台常规布局）。

### 7.5 遗留项（未做，需你先定）

1. **`aoqun-ming`（明制袄裙）无素材**：按计划 B 选项暂时指向 `mamian-qun`；真正补一件需要走一轮 ImageGen + `register_garments`。
2. **本地 `.env` 不动**（按你的定：本地库先不改）：平台 8765 本机仍起不来，首页依赖它的两个接口会报 Network Error。
3. **P6 候选**（计划里已标为非必需）：`DELETE /api/v1/history/{task_id}`、`user_costume_log` 加 `tryon` 动作、鉴权/签名 URL、把模块 scoped 样式改读平台 CSS 变量。
4. **磁盘上的旧结果文件不会自己搬**：若生产真把 `results_root` 换到 `backend/uploads/tryon`，需一次性拷贝 `tryon_service/data/results/` 下已有目录（读取层只改写 URL）。
