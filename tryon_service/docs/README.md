# 衣溯AI · 虚拟试穿模块（Web 全栈）

> 上传一张真人照片 → 从馆藏汉服素材库选一件 → 得到贴合肩线/腰线/衣摆的试穿效果图，
> 同时看到「人像分割 → 姿态关键点 → 服饰形变 → 遮挡还原/光影匹配 → 落盘入库」的全部中间产物与史料溯源卡片。

**核心特性**

- **可插拔推理**：`VTON_BACKEND=auto|aidge|hrviton|tps|mock`，`auto` 按 `aidge → hrviton → tps → mock` 探测可用性并**显式记录降级原因**，绝不静默失败。`aidge` 是云端生成式后端（阿里云 Aidge 虚拟试穿），没配凭据时自检即不可用，本机与生产都能原样退回本地 TPS。
- **零权重也能出图**：默认路径 TPS（薄板样条）纯 CPU、不依赖任何 `.pth/.onnx`，无 GPU 的笔记本即可跑通端到端。
- **Provider 链**：人像分割（VitonGPCI → U2Net → MediaPipe Selfie → GrabCut 启发式）与姿态（MediaPipe PoseLandmarker → mask 几何反推）逐项自检，有就用、没有就退。
- **工程健壮性**：请求级 `request_id` 贯穿日志、上传真实格式校验（拒绝伪扩展名）、错误响应脱敏（`error_code` + 中文 `message` + `detail`（同值别名）+ `request_id`）、磁盘结果缓存（命中会明确告知，也可 `force_refresh` 强制重算）。
- **答辩友好**：中间图（mask / pose overlay / warped garment）全部落盘并可通过 `/tryon-results/...` 直接访问。

本机实测环境：Windows + Python 3.10.11 + Node v24.19.0，**无 GPU、无任何 AI 权重**，TPS 兜底端到端出图 ≈ 1.6–2.9 秒。

---

## 一、目录结构

```
chat-1/
  README.md                  本文件（快速开始 / 接口 / 排障）
  PROJECT_DOC.md             项目书可直接粘贴章节（流程图 / 方案对比 / 局限性 / 部署）
  backend/
    requirements-core.txt    fastapi uvicorn pillow numpy scipy opencv-python-headless ...
    requirements-ai.txt      mediapipe onnxruntime（可选，提升分割与姿态精度）
    requirements-gpu.txt     torch/torchvision + HR-VITON 说明（可选）
    requirements-dev.txt     pytest httpx
    .env.example             全部配置项示例（复制为 .env 即生效）
    app/
      main.py                create_app() + lifespan（建目录→建表→种子→挂静态）
      config.py schemas.py logs.py errors.py
      db/{base,models,repos}.py
      services/
        segmentation/        vitongpu / u2net / mediapipe_selfie / heuristic 四级链
        pose/                MediaPipe Tasks PoseLandmarker + mask 几何兜底
        vton/                hrviton / tps(+tps_math) / mock / harmonize + resolve() 选择器
        postprocess/         边缘羽化 + 轻度降噪 + 可选锐化
        garments/            素材加载与严格校验 + 纯色底抠图 + 无标注服饰的 9 关键点自动推断
        pipeline.py          编排：分割→姿态→形变→合成→后处理→落盘
        history.py seed.py
      api/{tryon,garments,history,health,debug,deps}.py
      utils/{imageio,upload,cv,static}.py
    scripts/                 gen_sample_garments / register_garments / seed_garments / init_db / doctor / download_weights
    tests/                   6 个测试文件，54 条用例
    data/{garments,garments_src,uploads,results,samples}/   weights/   logs/
  frontend/
    vite.config.ts           dev proxy：/api/v1・/tryon-assets・/tryon-results → 127.0.0.1:8000
    src/
      api/{client,tryon,garments,health}.ts    Axios + 重试 + AbortSignal + 字段守卫
      utils/{compressImage,guards,snapshot}.ts Canvas 压缩 + 响应校验 + 截图落盘
      store/{app,tryon}.ts   Pinia（素材/健康状态、试穿状态机与进度插值）
      components/            ImageUploader / GarmentPicker / PipelineStepper / ResultViewer / TraceCard
      views/                 TryOnView / GalleryView / HistoryView / NotFound
      styles/variables.css   朱红 · 墨黑 · 宣纸米 主题变量
  oneoff/                    端到端截图留档（索引见本文第六节）
  scripts/dev-start.ps1      一键起（Windows）  dev-stop.ps1  停止
          dev-start.sh       一键起（macOS/Linux）
```

---

## 二、快速开始

### 2.1 Windows（PowerShell，推荐）

```powershell
cd <项目根>
.\scripts\dev-start.ps1            # 建 venv → 装核心依赖 → 生成示例素材 → 体检 → 起前后端
.\scripts\dev-start.ps1 -WithAI    # 追加 mediapipe + onnxruntime（更准的分割/姿态）
.\scripts\dev-start.ps1 -Mirror    # 网络受限时走清华 / npmmirror 镜像
.\scripts\dev-stop.ps1             # 结束 8000 / 5173 端口进程树
```

### 2.2 macOS / Linux

```bash
./scripts/dev-start.sh                 # 同上
WITH_AI=1 MIRROR=1 ./scripts/dev-start.sh
```

### 2.3 手动分步（排查问题时用这个）

```powershell
# 后端
cd backend
py -3.11 -m venv .venv ; .\.venv\Scripts\Activate.ps1
pip install -r requirements-core.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install -r requirements-dev.txt                # 想跑测试才需要
pip install -r requirements-ai.txt                 # 可选：mediapipe + onnxruntime

python -m scripts.gen_sample_garments --with-person   # 零素材时的兜底：程序化绘制 6 件示意图 + 示例人像（index.json 已存在则只跳过绘制）
python -m scripts.seed_garments                       # upsert 入 SQLite
python -m scripts.doctor --selftest                   # 打印 Provider 可用矩阵并真跑一遍出图
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# 前端（另开终端）
cd frontend
npm install
npm run dev            # http://127.0.0.1:5173
npm run typecheck      # vue-tsc 严格模式，0 error
npm run build          # 产物 dist/
```

启动后：

| 入口 | 地址 |
| --- | --- |
| 前端 | http://127.0.0.1:5173 |
| 后端 OpenAPI | http://127.0.0.1:8000/docs |
| 健康检查 | http://127.0.0.1:8000/api/v1/health |

前端页面上点 **使用示例人像 → 选一件素材 → 一键试穿** 即可出图，不需要任何真实照片或 GPU。

---

## 三、配置项（`tryon_service/.env`，全部有代码默认值）

> 文件位置以代码为准：`app/config.py` 里 `BACKEND_ROOT = Path(__file__).resolve().parent.parent`，
> `env_file` 因此是 **`tryon_service/.env`**，不是平台的 `backend/.env`。
> 把 `YISU_AIDGE_*` 填进 `backend/.env` 会被完全忽略，云端后端仍然报 `missing_credentials`。
> 生产那份由 `cloud_deploy_tryon.py` 的 env 阶段就地生成（0600），脚本只重写自己维护的几个键，
> 人工加的 `YISU_AIDGE_ACCESS_KEY_*` / `YISU_PUBLIC_BASE_URL` 原样保留，并打印 `PRESERVED ...` 供核对。

| 变量 | 默认 | 说明 |
| --- | --- | --- |
| `YISU_VTON_BACKEND` | `auto` | `auto / aidge / hrviton / tps / mock`；`auto` 会按优先级探测并降级 |
| `YISU_AIDGE_ACCESS_KEY_ID` / `_SECRET` | 空 | 云端试衣凭据。**只走 `.env`（0600）或 systemd Environment，别写进全局可读的 unit 文件，更不进仓库**；缺任一即 `available()=False`，流水线自动降级 |
| `YISU_PUBLIC_BASE_URL` | 空 | 厂商能回访到的本服务地址，如 `http://47.93.14.11`。云端接口只收公网图片 URL，人像要先经 `data/outbox/` 换成一次性地址 |
| `YISU_AIDGE_RESOLUTION` | `1K` | `1K` / `2K`，接口必填档位；2K 单价更高 |
| `YISU_AIDGE_CLOTH_TYPE` | 空 | 留空按素材 `category` 推导（robe/dress→dresses、top→tops、skirt→bottoms）。实测厂商的 Auto 会把汉服大袖袍认成现代上衣，所以不建议交给它 |
| `YISU_OUTBOX_TTL_SECONDS` | `600` | 出箱图片的存活上限；正常路径在试穿调用结束（`finally` 里 discard）时就删，这一档只兜进程崩溃。**不做读后即删**——厂商会 HEAD 预检、会重试，nginx 对 HEAD 还会多打一次上游，任何多余读取都会把真正取图那次打成 404 |
| `YISU_DATABASE_URL` | 空（由 `platform_db_path` 推导） | 默认跟平台主库同一个 SQLite 文件；生产改 `mysql+aiomysql://...` 即切 MySQL，无需改代码 |
| `YISU_PLATFORM_DB_PATH` | `../backend/data/yisu_prod.db` | 并入形态下指向平台主库；单独跑本模块时它就在 `backend/data/` 下 |
| `YISU_SQLITE_WAL` | `false` | 默认不开 WAL：WAL 是写进库文件的持久设置，且会多出 `-wal/-shm` 旁文件，平台有按单文件拷贝库的习惯 |
| `YISU_DATA_DIR` / `YISU_WEIGHTS_DIR` | `./data` / `./weights` | 素材、上传、结果、日志的根目录 |
| `YISU_MAX_UPLOAD_MB` | `12` | 单张图片上限；JSON 请求体按 Base64 膨胀放宽到 2.2× |
| `YISU_OUTPUT_LONG_SIDE` | `1024` | 输出长边，`hd` 模式不缩小、`fast` 模式按需缩放 |
| `YISU_FORCE_CPU` | `false` | 有 CUDA 也强制走 CPU，便于对比测试 |
| `YISU_VITONGPU_ONNX` / `YISU_U2NET_ONNX` / `YISU_HRVITON_CKPT_DIR` | `weights/...` | 可选权重路径，缺失只降级不报错 |
| `YISU_CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | 只放行本地前端 |
| `YISU_ENABLE_DISK_CACHE` | `true` | 同人像 + 同素材 + 同画质命中时直接复用上次结果（`warnings` 会带 `result_from_cache`） |
| `YISU_ASSET_URL_PREFIX` | `/tryon-assets` | 素材图/示例图的对外前缀（两个窄挂载：`/garments`、`/samples`） |
| `YISU_RESULTS_URL_PREFIX` | `/tryon-results` | 结果图/中间图的对外前缀；交给平台 nginx 时改 `/uploads/tryon` |
| `YISU_RESULTS_ROOT` | 空（= `<data_dir>/results`） | 结果图落盘根目录。指到 `data/` 外（如平台 `backend/uploads/tryon`）时，本服务不再挂结果前缀，改由宿主提供 |

> 刻意**不做内存缓存**：`garment_id + png` 作 key 的内存缓存极易膨胀，改为磁盘缓存 + 结果复用。

---

## 四、接口一览

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| POST | `/api/v1/tryon` | 主接口，JSON + Base64（前端压缩后提交） |
| POST | `/api/v1/tryon/upload` | 等价能力，`multipart/form-data`，便于 curl / 文档演示 |
| POST | `/api/v1/tryon/batch` | 批量连续试穿（1–8 件，单件失败不影响整体） |
| GET | `/api/v1/tryon/{task_id}` | 结果查询 / 轮询 |
| GET | `/api/v1/tryon/meta/segmentation` | 分割 Provider 实时状态（调试面板） |
| GET | `/api/v1/garments` · `/api/v1/garments/{id}` | 素材列表（支持 `category` / `dynasty` / `keyword` 过滤）与详情 |
| GET | `/api/v1/garments/{id}/trace` | 史料溯源卡片数据（`source_text` + `references`） |
| GET | `/api/v1/history?limit=&offset=` | 试穿记录分页 |
| GET | `/api/v1/health` | 逐项依赖体检（见 4.3） |
| GET | `/api/v1/debug/skeleton` | 截图留档用的页面骨架 + 运行环境元数据 |
| GET | `/tryon-assets/garments/...`・`/tryon-assets/samples/...` | 素材图与示例图（两个窄挂载，只读） |
| GET | `/tryon-results/...` | 结果图与管线中间图；并入平台后可整体改指 `/uploads/tryon` 交给平台 nginx |

> 旧版把整个 `data/` 挂在 `/static` 下，已在并入平台时撤掉（`data/uploads` 是上传原图的临时落盘，不该被 URL 直读）。
> 库里残留的 `/static/...` 旧地址在历史/缓存读取层自动改写，详见第十二节。

### 4.1 curl 示例

```bash
# Base64 JSON
python - <<'PY'
import base64, json, urllib.request
person = base64.b64encode(open("backend/data/samples/person_demo.png","rb").read()).decode()
body = json.dumps({"person_image": f"data:image/png;base64,{person}",
                   "garment_id": "quju-shenyi", "quality": "fast"}).encode()
req = urllib.request.Request("http://127.0.0.1:8000/api/v1/tryon", data=body,
                             headers={"Content-Type": "application/json"})
print(json.loads(urllib.request.urlopen(req).read()))
PY

# multipart
curl -F person_file=@person.jpg -F garment_id=beizi -F quality=hd \
     http://127.0.0.1:8000/api/v1/tryon/upload
```

`TryOnResult` 字段：`task_id, status, result_url, person_mask_url, pose_overlay_url,
garment_warp_url, backend_used, warnings[], timings{}, trace_card, error_code, message`。

### 4.2 请求字段与磁盘缓存

三个提交端点共用同一组可选字段：`quality`（`fast` / `hd`）与 `force_refresh`（默认 `false`）。

流水线是**确定性**的，缓存键为 `sha256(人像像素 + 服饰图 + 服饰 mask + 素材 id + quality)`，
落在 `data/results/{task_id}/cache_*.json`。所以**同一张照片 + 同一件素材 + 同一画质再点一次，
返回的一定是同一张图**，响应里会多一条 `result_from_cache` 告警，`timings` 回传的是首次真实
推理的记录值（不代表这次只花了这么点时间）。想强制重算：

```bash
curl -X POST http://127.0.0.1:8000/api/v1/tryon \
     -H 'Content-Type: application/json' \
     -d '{"person_image": "...", "garment_id": "quju-shenyi", "force_refresh": true}'
```

`force_refresh=true` 会跳过查表真跑一次推理，并附带 `cache_bypassed` 告警（该告警只出现在这次
的响应里，不会被写进历史记录）。前端对应「跳过缓存强制重算」开关，命中缓存时会弹出提示条。

### 4.3 健康检查读法

`status=degraded` **是正常状态**：表示「有依赖缺失但已降级到可用路径」。真正需要关注的是
`components.vton.resolved_auto.backend`（当前实际生效的推理后端）与每个 provider 的 `reason`。

---

## 五、算法路径与降级矩阵

```
真人照(Base64) → 长边≤1024 归一 / EXIF 转正
   ├─ 人像分割：vitongpu → u2net → mediapipe_selfie → heuristic(GrabCut + 中心前景先验)
   ├─ 姿态估计：MediaPipe PoseLandmarker(33→COCO-17) → 由 mask 宽度分布反推肩线/腰线/衣摆
   ├─ 试穿推理：aidge(云端生成式，需凭据+公网回取) → hrviton(GPU + 双权重) → tps(9 对控制点薄板样条 + 遮挡还原 + LAB 亮度匹配) → mock
   └─ 后处理：1–3px 边缘羽化 + 轻度降噪 + 可选锐化（不做全局平滑，保留衣纹）
```

**TPS 兜底细节**（`app/services/vton/tps.py`）

1. 目标锚点由姿态结果构造：肩宽比 `s = person_shoulder_width / garment_shoulder_width`，躯干长度映射衣长，肩→肩、腰→腰、摆→摆共 9 对控制点。
2. TPS 求解（`tps_math.py`，`scipy.linalg`）→ 逐像素映射服饰 RGB 与 mask。
3. 遮挡处理：把人体语义 mask 中的手臂/头部区域在服饰之上**重新贴回**，避免「衣服盖住手臂」。
4. 光影匹配：目标身体区域的 LAB 亮度 gain 匹配 + `cv2.seamlessClone` 羽化边界。
5. 输出 `garment_warp.png` 中间图，供「几何变形 → 渲染 → 合成」三步展示。

**当前这台机器的实际路径**（`doctor` 输出摘要）

| 环节 | 生效实现 | 降级原因 |
| --- | --- | --- |
| 分割 | `heuristic` | vitongpu/u2net 权重缺失、`onnxruntime`/`mediapipe` 未装 |
| 姿态 | mask 几何反推 | `mediapipe` 未装 |
| 推理 | `tps` | `torch` 未装（装上权重 + CUDA 后 `auto` 自动切 `hrviton`） |
| 后处理 | 羽化 + 锐化 | — |

---

## 六、截图留档索引（`oneoff/`）

截图由浏览器实际渲染产生（未引入 Playwright），配合 `GET /api/v1/debug/skeleton` 的 JSON 元数据归档：

| 文件 | 内容 |
| --- | --- |
| `step1_home_full.png` | 首屏：上传区 + 效果输出区 + 6 件素材卡片 † |
| `step2_sample_portrait_loaded.png` | 载入示例人像（压缩尺寸/体积回填） |
| `step3_tryon_result_full.png` | 一键试穿完成：结果大图 + 阶段耗时 + 告警面板 + 溯源卡 † |
| `step4_pipeline_middle_images.png` | 管线中间图面板：mask / 17 关键点 / 形变结果 |
| `step4_home_full_with_panel.png` | 展开中间图后的整页 † |
| `step5_gallery_drawer_trace.png` | 素材库详情抽屉：史料溯源（`source_text` + `references`） |
| `step5_gallery_dialog_viewport.png` | 素材库详情（视口） |
| `step6_history_full.png` | 试穿记录列表（结果图 + 原图 + 后端/画质标签 + 告警数） |
| `step7_404_page.png` | 404 页面（非白屏，带导航按钮） |
| `real_step2_sample_portrait_loaded.png` | **真实质感重验**：载入 `person_real.png`（683×1024，689.5 KB → 42.2 KB） |
| `real_step3_tryon_result_full.png` | **真实质感重验**：曲裾深衣试穿结果 + 「TPS 几何兜底（CPU）」标签 + 7 条告警面板 |
| `cache_alert.png` | **缓存可见性**：同一组合再点一次 → 黄色提示条 + info 弹窗 + 告警列表中文标签（`result_from_cache`） |
| `force_refresh.png` | **跳过缓存强制重算**：勾选开关后提示条消失、改为 success 弹窗、告警变 `cache_bypassed`、结果落到新 task 目录 |

> `real_*` 两张是素材换成真实质感汉服 + 真人像之后的复验图：交领位置正确、广袖垂在手臂外侧、衣摆至膝下，
> console 0 error / 0 warning；残留瑕疵见 `PROJECT_DOC.md` 第 6 节第 5 条（肩袖处会露出原衣、贴图式直切边）。

> † 这三张是**首轮**端到端验证时拍的整页图，当时筛选下拉还显示内部哨兵值「全部品类（`__all__`）」；
> 该问题（以及步骤条末步无成功态、完成后文案回落「等待提交」）已修复并经 DOM 级复验，
> 重拍需把浏览器窗口置于前台（窗口最小化时 CDP 拿不到渲染帧）。
> 制作答辩材料时建议用**视口截图**：`fullPage` 模式会把 sticky 头部重绘到页面中部。

---

## 七、测试

```powershell
cd backend ; .\.venv\Scripts\python.exe -m pytest -q      # 56 passed
```

| 文件 | 覆盖点 |
| --- | --- |
| `test_api_contract.py` | `TryOnResult` 全字段、四张中间图可下载、批量、multipart、历史分页、404/422 脱敏、磁盘缓存命中与 `force_refresh` 跳表 |
| `test_segmentation_fallback.py` | Provider 链逐层降级仍产出合法 mask，且 `warnings` 记录降级原因 |
| `test_vton_backend_selection.py` | `auto` 优先级、指定后端不可用时的显式报错、运行期异常继续降级 |
| `test_garments_validate.py` | bbox 面积比 0.05–0.95、关键点数=9、ID/名称合法性、去重 |
| `test_upload_guard.py` | 伪造扩展名拒绝、超限拒绝、EXIF 转正、长边归一 |
| `test_db_contract.py` | `database/tryon_schema.sql` 的 DDL 与两侧 ORM（模块 async / 平台 sync）列集合一致，防定义漂移 |

---

## 八、可选权重（装了就自动升级精度，不装完全能跑）

```powershell
cd backend
python -m scripts.download_weights --list           # 查看白名单资产与当前到位情况
python -m scripts.download_weights --asset u2net    # 官方直链 + .part 续传 + 原子 rename + 可选 SHA256
python -m scripts.download_weights --asset u2netp   # 4MB 轻量版，CPU 上更快
python -m scripts.download_weights --asset vitongpu --url https://<白名单内直链>
python -m scripts.download_weights --asset hrviton  # 打印获取指引（官方不直发权重）
```

- HR-VITON 需要 `weights/hrviton/mtviton_step_100000.pth` + `gen_step_110000.pth` **且** `torch` 可导入 **且** CUDA 可用，三者齐备才启用；推理失败会回原图 + 画错误框 + `warnings=["hrviton_inference_failed", reason]`。
- 仓库**不提交任何** `.pth/.onnx/.pt`（见 `.gitignore`）。
- Google Drive 来源请用浏览器手动下载后放入 `backend/weights/`。

## 九、替换成真实馆藏素材

### 9.1 一条命令接入任意图片（推荐）

`scripts/register_garments.py` 把「一张普通图片」变成「可试穿素材」：自动抠图 → 裁剪 → 推断 9 关键点 →
写 `{id}.png/_mask.png/_thumb.png` → upsert `index.json` → 可选立即出预览图。

```powershell
cd backend
# 单件：广袖/曲裾类用 robe，裙类用 skirt，短襦类用 top
python -m scripts.register_garments --image ../raw/quju.png --id quju-shenyi `
  --name 曲裾深衣 --dynasty 汉代 --category robe --tags 深衣,曲裾,广袖 --preview

# 批量：清单里写 person + garments，一次注册全部并顺带替换示例人像；--seed 会 force 覆盖入库（keypoints 已变）
python -m scripts.register_garments --manifest data/garments/real_manifest.json --preview --seed

# 只换示例人像，不动素材库
python -m scripts.register_garments --person ../raw/model.png
```

- 抠图逻辑在 `services/garments/matting.py`：边框采样估背景色 → 色差图 Otsu → **边缘带弱对比剔除**（水印/角标/拍台阴影）→ 闭运算 → 填洞 → 最大连通域 → 分位数二次收紧。
- 关键点逻辑在 `services/garments/auto_annotate.py`：由掩码推 `collar_center / shoulder_L,R / sleeve_L,R_end / waist_L,R / hem_L,R`；`skirt` 品类会把上身 7 点压到裙腰带，交给 TPS 按人体腰臀展开。
- 原始大图放 `data/garments_src/`（已 gitignore，不入库），成品在 `data/garments/`。
- 自带 alpha 通道的图直接沿用透明通道，不跑抠图；纯色底拍得不干净时加 `--force-salience` 走强显著性路径。

### 9.2 仓库自带的真实质感示例

`data/garments/index.json` 默认 6 件即来自该流程的**真实质感汉服**（曲裾深衣 / 齐胸襦裙 / 圆领袍 / 褙子 / 马面裙 / 唐半臂），示例人像为 `data/samples/person_real.png`；前端「使用示例人像」与 `doctor --selftest` 都按 `person_real.png → person_demo.png` 顺序取图。Pillow 画的几何示意图仍由 `gen_sample_garments.py` 保留，作为零素材时的兜底。

> 这些图由生成式模型产出，人像右下角保留了平台的「AI 生成」角标，**未做去标识处理**；若要用于对外演示，请换成自行拍摄或有授权的真人照片与服饰图（`--person` / `--image` 就是为此准备）。

### 9.3 手工编辑索引

1. 把图片放入 `backend/data/garments/`（如 `my-garment.png`），可选放同名 `_mask.png` / `_thumb.png`。
2. 在 `backend/data/garments/index.json` 追加一条：`id,name,dynasty,category,tags,image,mask,keypoints,source_text,references`，其中 `keypoints` 为 9 个归一化点：
   `collar_center, shoulder_L, shoulder_R, sleeve_L_end, sleeve_R_end, waist_L, waist_R, hem_L, hem_R`。
3. `python -m scripts.seed_garments` 重新入库。校验失败的素材**只跳过并记 warning**，不会阻断启动。
4. 没有手标关键点时，临时上传（`garment_image` / `garment_file`）会走 `auto_annotate.infer_keypoints_from_mask` 由掩码自动推断同样 9 个点。

---

## 十、常见问题

| 现象 | 原因与处理 |
| --- | --- |
| `pip` 报 `RemoteDisconnected` | PyPI 直连不稳，加 `-i https://pypi.tuna.tsinghua.edu.cn/simple`（或 `dev-start.ps1 -Mirror`） |
| PowerShell 里跑脚本返回 `ExitCode 1` 但输出正常 | uvicorn/Python 把日志写 stderr，PowerShell 会当成 `NativeCommandError`。以脚本自身打印的 `[selftest] 通过` / `LASTEXITCODE` 为准 |
| 健康检查 `status=degraded` | 正常，表示已降级到 CPU 兜底路径；`vton_backend_resolved=tps` 即能出图 |
| 结果图里服饰偏上/偏下 | 正身、肩部完整、光线均匀的照片效果最好；侧身或抬手会削弱贴合度（见 `PROJECT_DOC.md` 局限性） |
| 真实照片抠图带进了水印/桌面阴影 | 重跑 `register_garments` 时加 `--force-salience`，或自备同名 `_mask.png`（抠图不依赖 mediapipe，纯 numpy/scipy） |
| 广袖/大摆被压成窄条 | 确认 `--category` 用对（`robe`/`dress` 才会按肩宽等比展开袖口，`top` 会被夹到髋膝之间） |
| 前端素材库空白 | 后端未启动或未生成示例素材：`python -m scripts.gen_sample_garments --with-person && python -m scripts.seed_garments` |
| 想强制走某条后端对比 | 在 `backend/.env` 设 `YISU_VTON_BACKEND=mock`（贴图基线）、`tps`（本地兜底）或 `aidge`（云端，缺凭据时会带着原因自动降级），重启后端 |
| 点了「一键试穿」结果图没变化 | 命中磁盘缓存，属预期行为：页面会可见提示（info 弹窗 + 结果区「命中磁盘缓存，本次未重跑推理」），不会静默复用。换素材 / 切 HD / 换照片，或勾选「跳过缓存强制重算」（接口传 `force_refresh=true`）才会真跑 |
| 图片 404 但文件已落盘 | 先看响应里的 URL 前缀：`/tryon-assets`・`/tryon-results` 需要在 vite dev proxy 或 nginx 里有对应转发；若只改了 `YISU_RESULTS_ROOT` 而没改 `YISU_RESULTS_URL_PREFIX`，启动日志会直接给出告警 |

## 十一、与计划的偏差说明

- **Element Plus 采用全量引入**（计划写的是「按需引入」）：为保证在无网络/弱网环境下 `npm install && npm run build` 一定成功，不引入 `unplugin-vue-components` 等额外构建期依赖；已用 `manualChunks` 把 `element-plus` 与 `vue` 生态拆成独立 chunk 缓解体积。
- 其余目录结构、接口、算法链、测试项与计划一致；`oneoff/` 截图用浏览器实际渲染 + `/api/v1/debug/skeleton` 元数据，未引入 Playwright。

---

## 十二、并入 yisu-ai-platform（sidecar 形态）

本模块已作为独立子服务合进平台仓（`D:\yisu-ai-platform`），本工作区仍是它的原始副本与开发沙盒。

### 12.1 布局

| 部分 | 位置 | 运行形态 |
| --- | --- | --- |
| 试穿后端 | `tryon_service/` | Python 3.10 独立 venv + uvicorn `127.0.0.1:8000`（**生产用 `:8010`**，8000 归 museum-api，见第十三节），与平台 `backend/`（Python 3.14、`:8765`、MySQL）**同仓不同进程**，所以 148 处 `from app.` import 一个字没改 |
| 试穿前端 | `frontend/src/tryon/` | 并入平台 SPA，路由 `/museum/tryon{,/gallery,/history}`，`TryonLayout.vue` 提供模块子导航与后端健康标签 |
| 数据库 | `backend/data/yisu_prod.db` | `tryon_garments` / `tryon_records` 两张表直接建在平台主库里；`database/tryon_schema.sql` 是列定义的唯一事实源 |
| 静态资源 | sidecar 挂载 | `/tryon-assets/{garments,samples}` ・ `/tryon-results`（生产可改指平台 `/uploads/tryon`） |

### 12.2 部署文件

- `yisu-tryon.service`：`User=www`（结果图要写进属 www 的 `backend/uploads/tryon`）、单 worker 有意（MediaPipe 模型与线程池在进程内）、`CPUQuota=150%` + `MemoryHigh=900M`（2 核 / 1.7G 的机器上给平台主服务与 MySQL 留一半），结果图指到 `backend/uploads/tryon`。
- `yisu_nginx.conf`・`yisu_nginx_limit.conf`：**这两份是线上实况的镜像**（由 `scripts/cloud_sync_nginx.py` 回拉，不要反向推回服务器）。`/api/v1/` 反代到 sidecar 并按 IP 限流（`limit_req_zone` 只能写 `http{}`，所以单独一个文件，宝塔把 `vhost/nginx/*.conf` include 进 `http{}`）；`/tryon-assets/` 长缓存 7d；结果图复用既有 `/uploads/` 规则，生产不必新增 location。
- `tryon_service/.env.example`・`requirements-mysql.txt`：生产切 MySQL 用的是**异步驱动 `aiomysql`**（平台侧同步 ORM 用 `pymysql`，两者互不影响）。
- **云端试衣的出箱路由已于 2026-10-20 上线**：`location /api/v1/outbox/` + 独立的 `zone=tryon_outbox:240r/m`，`yisu_nginx.conf`・`yisu_nginx_limit.conf` 两份镜像已用 `cloud_sync_nginx.py` 回拉成实况。为什么单开一条：`/api/v1/` 的 `limit_req` 按 `$binary_remote_addr` 分桶、20r/m，而出箱图是**厂商服务器**来取的，这一桶记的是阿里云出口 IP，被 503 掉的表现是「URL 发出去了但厂商没取到图」，长得像模型故障。上线后实探：`GET /api/v1/outbox/<合法但不存在的 token>` 回 `{"error_code":"TASK_NOT_FOUND",...}` 404，说明 nginx 与路由都通。
- 判断这条通了没：`curl -i http://47.93.14.11/api/v1/outbox/probe0000000000000000`。**404 + JSON = 通**（请求到了 FastAPI，路由在，只是这个 token 不存在）；503 = 被 `limit_req` 挡着，正是单开 location 要解决的；nginx 自带的 HTML 404 或连不上 = 根本没打到 sidecar（`PUBLIC_BASE` 那个 IP 归了别的 server 块，或 `/api/v1/` 那条 location 被人改过）。`stage_verify` 已把这条做成硬失败，不花钱也不需凭据。

### 12.3 开发时的四个坑（踩过，写在这儿防重复踩）

1. **命名空间包串门**：平台的 `backend/app` 没有 `__init__.py`（命名空间包），而 `tryon_service/app` 是常规包；`PYTHONPATH` 残留会让一侧进程 import 到另一侧的 `app`，平台 venv 缺 `greenlet`，于是去加载 `sqlalchemy.ext.asyncio` 直接报错。跑任何一侧重试前先 `$env:PYTHONPATH=""`。
2. **`vue-tsc -b` 会生成陈旧 `vite.config.js`**：Vite 找配置时 `.js` 优先于 `.ts`，导致改 `.ts` 里的代理完全无效。已在 `tsconfig.node.json` 设 `outDir` 根治，产物不再落在源码旁。
3. **主题变量**：模块只用 `--yisu-*`，原来对 `--el-*` 的全局覆盖已在并入时删掉，主色交给平台；两边变量命名空间不冲突。
4. **不要用 `meta.bareLayout`**：平台的 `.app-main.bare` 是 `height:100vh;overflow:hidden`，素材库这种长页会被整块裁且滚不到；试穿路由走平台常规布局（`max-width:1360px` + 自带内边距）。

### 12.4 残留风险（如实说明）

本服务**没有鉴权**，`/api/v1/history` 返的是全局列表；结果目录里存着 `person_source.jpg`（历史页要做原图对比），所以拿到他人 `task_id` 仍能看到那张人像。静态面收窄只解决了“上传原图目录 `data/uploads` 被整目录直读”，多租户开放前必须加访问控制或签名 URL。

### 12.5 提交账与回滚

```
(tag pre-tryon-merge)  合并前基线
25aede9  P1  sidecar 迁入（87 文件）
5c72aea  P2  两张表并入平台库 + schema 契约测试
add4a5b  P3  前端并入 src/tryon（28 文件）
e60edfc  P4  静态面拆分 + 部署装配
cfa3cff  P5  两侧测试/构建/端到端复验 + 文档归位
```

回滚：`git revert` 对应提交，或本地直接 `git reset --hard pre-tryon-merge`；数据面 `DROP TABLE tryon_records; DROP TABLE tryon_garments;`（只有这两张表新增，未改平台既有表），再删 `tryon_service/` 与 `frontend/src/tryon/`。

---

## 十三、云端（生产）部署实录 —— 阿里云 ECS

2026-10-16 落地。约束是：把 sidecar 装进**已经在跑平台主服务的那台机器**，不新建服务器、不停平台进程、不碰宝塔面板维护的部分。

### 13.1 勘察出的事实，以及由它们定下的参数

| 实测事实 | 由此确定的做法 |
| --- | --- |
| Ubuntu 22.04 · 2 vCPU · 1.7G 内存（available 862M）+ 1G swap · 磁盘约 13G 可用 | 不装 torch（HR-VITON 上不去），走 TPS 几何兜底；`CPUQuota=150%` + `MemoryHigh=900M` |
| 系统 `python3.10.12`；平台主服务是 Python 3.14 | sidecar 自建 `.venv`（mediapipe 在 3.14 无可用轮子，且 numpy/opencv 版本互相冲突） |
| **8000 已被 `museum-api.service` 占用**（nginx `/museum/api/` → 它） | sidecar 生产端口 **8010**；开发默认仍是 8000 |
| MySQL 5.7.43 的 `yisu_ai` 库里 `tryon_garments` / `tryon_records` **已存在**（0 行，列与我们 DDL 一致） | 不重建、不动表，只 `init_db --seed` 把 6 件素材写进去 |
| 站点 conf 由宝塔维护，含 `/museum/api/`、`location = /museum`、`/index.html` 不缓存等模板里没有的东西 | 部署只**备份 + 锚点插入**，绝不整体覆盖；改完用 `cloud_sync_nginx.py` 把实况回拉成仓库镜像 |
| `nginx.conf` 把 `vhost/nginx/*.conf` include 进 `http{}` | `limit_req_zone` 单独放 `tryon_limit.conf`，不必改面板维护的 `nginx.conf` |
| `frontend/dist` 里已有 `TryOnView` / `TryonLayout` / `tryon` chunk（路由 `/museum/tryon`），服务器无 node | 前端不重新构建，产物已在位 |
| 结果图目录 `backend/uploads/tryon` 属 www，nginx 已有 `/uploads/` alias | `YISU_RESULTS_ROOT` + `YISU_RESULTS_URL_PREFIX=/uploads/tryon` **成对改**，生产不新增静态 location；unit 里 `User=www` |

### 13.2 重跑方式

```powershell
python scripts\cloud_deploy_tryon.py <stage>   # 单跑一个阶段
python scripts\cloud_deploy_tryon.py all       # 按顺序全跑
```

八个阶段各自幂等：`upload`（打包平台 `tryon_service/`，排除 venv/日志/`.env`/运行时数据）→ `venv`（py3.10 建环境，装 core + ai + mysql）→ `env`（**数据库口令只在服务器侧从 `backend/.env` 就地读取**，生成 `tryon_service/.env` 并 chmod 600，本机不留副本）→ `dirs` → `seed` → `service` → `nginx` → `verify`。

SSH 凭据也不写在脚本里，而是用正则从平台既有部署脚本 `_deploy_backend.py` 里读。

- nginx 阶段先 `cp yisu.conf yisu.conf.bak.<时间戳>`，再 `nginx -t`；**测试不通过会自动还原最新备份并中止**，不会留下坏配置。
- 回滚单阶段：`systemctl stop yisu-tryon.service` + 还原 `.bak` + `nginx -t && systemctl reload nginx`，平台主服务与博物馆接口不受影响。
- `python scripts\cloud_sync_nginx.py --diff` 看仓库镜像与线上的差异，去掉 `--diff` 就回拉落盘。

### 13.3 部署过程炸出来的三个真实缺陷

这三个都不是云端特有的偶发故障，而是只有生产环境才会暴露的代码/依赖缺陷，已全部回写到开发侧并加了防复发措施：

| 现象 | 根因 | 修法 | 防复发 |
| --- | --- | --- | --- |
| 服务根本起不来：`SettingsError: error parsing value for field "cors_origins" from source "DotEnvSettingsSource"` | `.env` 里写 `YISU_CORS_ORIGINS=`（同源部署清空的常见写法）。`list[str]` 是复杂类型，pydantic-settings 在 **source 层**先按 JSON 解码，空串不是合法 JSON，配置对象都构造不出来 | `config.py` 用 `Annotated[list[str], NoDecode]` + `mode="before"` 自己逗号切分 | `test_empty_cors_origins_env_is_accepted`（含用 `Settings(_env_file=...)` 精确复现 dotenv source）；`.env.example` 写清空值语义 |
| 连上生产 MySQL 后取连接就炸：`AsyncAdapt_aiomysql_connection.ping() missing 1 required positional argument: 'reconnect'` | SQLAlchemy 2.0.36 的 aiomysql 适配层签名是 `ping(self, reconnect)` 无默认值，而 `MySQLDialect_pymysql.do_ping` 在 `_send_false_to_ping=False` 时调的是无参 `ping()`；开了 `pool_pre_ping` 必炸。2.0.54 上游已改成 `ping(self, reconnect: bool = False)` | `requirements-core.txt` 把 `SQLAlchemy[asyncio]` 从 2.0.36 锁到 **2.0.54**（本地/平台/云端三处 venv 同步升级） | `test_db_contract.py` 加 `SQLALCHEMY_FLOOR=(2,0,54)` 版本地板测试。**本机走 sqlite 完全复现不了**，只能靠断言拦住降级 |
| `pip install` 近 20 分钟装不完 | mediapipe 对 `opencv-contrib-python` **没有版本约束**，pip 从 5.0.0.93 往下逐个回溯，每个 80MB | 显式锁 `opencv-contrib-python==4.11.0.86`（与本地实测一致），重跑 4.5 分钟完成 | 锁定写进 `requirements-ai.txt` 并附「为什么不能放开」注释 |

**2026-10-20 追加：`stage_verify` 的磁盘缓存假绿。** 之前 verify 的试穿 payload 没带 `force_refresh`，重跑时 0.2s 命中上一轮的磁盘缓存，返回的是**旧的 tps 结果**——云端链路到底通没通完全没测到，还会把旧图当成本轮出图存进 `tryon_qa/`。现在：payload 固定 `force_refresh: true`；先读 `/api/v1/health` 的 `vton_backend_resolved`，若解析为 `aidge` 而实际 `backend_used` 不是 `aidge`（降级）或 warnings 出现 `result_from_cache`，一律硬失败。用本地桩实测 5 个场景：云端正常 PASS、缓存命中 FAIL、aidge→tps 降级 FAIL、tps 正常 PASS、health 打不开 FAIL。注意：配置了云端后，每次 verify 会真实消耗一次云端额度（这是刻意的，否则测不到云端）。

### 13.4 上线验证记录（均为公网实测，非本地推断）

```text
systemd     active (running) · enabled（开机自启）· Memory 233M / high 900M · Main PID 跑 --host 127.0.0.1 --port 8010
ss -lntp    LISTEN 127.0.0.1:8010（8000 仍归 museum-api，两者共存）

GET  /api/v1/health                          200  1598B   vton_backend_resolved=tps · mediapipe_selfie available
GET  /api/v1/garments                        200  7266B   6 件素材
GET  /tryon-assets/garments/quju-shenyi.png  200  883815B image/png
GET  /api/home/stats                          200  51B     平台接口未被 /api/v1/ 抢走
POST /api/v1/tryon                            200  首跑 3.6s（真推理）· 重跑 0.2s（命中磁盘缓存）
GET  /uploads/tryon/<task>/result.jpg         200  44622B  image/jpeg

浏览器 /museum/tryon：页面正常渲染，6 张缩略图全 200，「使用示例人像 + 对襟褙子 + fast」
              → 页面提示「试穿完成（后端 tps，总耗时 2.12s）」，结果图与三张管线中间图全 200
              28 条资源请求无 4xx/5xx，控制台无页面报错
```

云端 MySQL `tryon_garments` 已有 6 行；`tryon_records` 随浏览器那一次试穿写入。

### 13.5 生产仍然不具备的东西（别把「能访问」读成「可开放」）

- **仍是 HTTP 裸端口 80 + IP 直连**，没有 HTTPS、没有域名；服务本身**依旧无鉴权**，12.4 列的风险在生产上同样成立。
- 限流 `20r/m` + `burst=5`（按客户端 IP）；2 核机器上 HD 画质会排队，`proxy_read_timeout` 已放宽到 300s。
- 默认推理后端已是 **Aidge 云端换装**（`/api/v1/health` 报 `aidge`），画质不再受 TPS 几何兜底限制；代价是**按张计费**，免费额度 30 张，未用量随时可能被前端某次「强制重算」烧掉。
- 云端结果与本地 TPS 结果共用同一套磁盘缓存键，**不含推理后端版本**：TPS 时代落过盘的组合（典型是示例人像 + 常见素材）会被直接命中，新访客第一次点击拿到的是本地几何兜底的旧图，前端只在标签上如实写「TPS 几何兜底」。要么清掉云端启用前的 `backend/uploads/tryon/*`，要么把后端版本纳入 `cache_key`。
- 结果图无 TTL 清理，磁盘只有 13G 可用；`/root/.cache/pip` 已占 4.3G，可以清。
- `backend/uploads/tryon/<task>/person_source.jpg` 随结果落盘，历史页要做原图对比 —— 对外开放前必须改成签名 URL。

### 13.6 3D 博物馆子站的「虚拟试穿」交接（已上线，2026-10-20 20:29）

线上 `/museum/` 整段由 3D 子站接管（nginx `location /museum/ { try_files /museum/index.html }`），子站自己打包了一个
`TryonPlaceholder` 占位组件挂在它的路由 `/tryon` 上。所以展厅卡片的「试穿此服饰」和顶部「虚拟试穿」都只会进那张占位页，
**不是链路坏，是子站根本没有真试穿页**。

**子站是 hash 路由**，这一条决定成败：真实形态是 `http://…/museum/#/tryon?garment=…`，展品参数在 `#` 之后、
不在 `location.search` 里。反过来，`http://…/museum/tryon?garment=…` 这种 pathname 写法**不会**触发子站路由，
index.html 加载后 router 直接把它归到 `#/museum`，那个 chunk 连加载都不加载。

实况与处置：

| 事实 | 值 |
| --- | --- |
| 动过的文件（唯一） | `dist/museum/assets/TryonPlaceholder-Bp1Rhoms.js`，现 1562 B、`root:root 644`、md5 `a3cf99881f4990c70540b191fe47a88b` |
| 原占位页备份 | 同目录 `TryonPlaceholder-Bp1Rhoms.js.bak.20261020_202732`（1595 B、666、md5 `e212ca98e5d5ece07c33dbcf52d9344f`） |
| 另一份备份 | `.bak.20261020_202920` = 交接模块 v1（只读 `location.search`，会把 `garment` 丢掉，已被 v2 覆盖掉，别当回滚点用） |
| 子站展品数据 | `assets/exhibits-Cb5qGZIp.js`：40 件里只有 4 件带 `tryonId`，其余 36 件的详情卡片压根不渲染按钮 |
| 其中两个标识与 sidecar 素材库对不上 | `yuanlingpao-tang` 应为 `yuanling-pao`、`beizi-song` 应为 `beizi`；交接模块里映射掉了 |
| 卡片按钮发出的东西 | `MuseumView-*.js`：`t.push({name:"tryon",query:{garment:D.tryonId,from:"museum"}})` |

**做法**：把那个 chunk 换成仓根的 `museum_tryon_handoff.js`（文件名不变，子站其它产物与 nginx 一行都没动），
模块里读 `search` 与 `hash` 两处参数、映射旧标识、补 `from=museum`，然后 `location.replace('/tryon?…')` 交给主站真页面。
载荷本身带注释与 `export default {render:()=>null}`，所以即便被 router 当组件用也不报错。

**已实测**（公网，2026-10-20 20:29–20:31）：

```
子站顶部「虚拟试穿」真点击  → http://…/tryon?from=museum        主站渲染、徽标「试穿服务正常 · Aidge 云端换装」
#/tryon?garment=quju-shenyi → /tryon?garment=quju-shenyi&from=museum  卡片 is-active=汉代曲裾深衣，toast「已选中展厅带来的「曲裾深衣」」
#/tryon?garment=beizi-song  → /tryon?garment=beizi&from=museum         旧标识映射生效，toast「已选中展厅带来的「对襟褙子」」
```

**没实测的一条**：展厅详情卡片上那个「试穿此服饰」按钮本身。它是 three.js 的 raycast 命中，内置浏览器用合成
PointerEvent 扫了 28 个坐标都没命中展品（`hasCard` 始终 false），我不拿「它 push 的 URL 我已验证可用」冒充点过它。
要确认就在真浏览器里点一次，它最终走的就是上面第二行那条 URL。

两个必须知道的边界：① 这是**服务器侧产物直改**，子站哪天重新构建上传就会被占位页盖回去，重推 `museum_tryon_handoff.js` 即可；
② `MuseumView-aROHavN7.js` 与 `index-BqJJw04H.js` 用户正在直接改（`_dl/` 里各有 `.bak` 且内容不同），
所以这个改动刻意只碰占位 chunk，不碰那两个文件，也不要用 `_up_mus3.py`（它硬编码上传的正好是那两个）。

还剩两笔可选账（都没做）：`/museum/tryon?garment=…` 这种 pathname 直达链接要能用，得给 nginx 加一条
`location = /museum/tryon { return 302 /museum/#/tryon$is_args$args; }`；子站另外 36 件展品要出按钮，得改它的
`exhibits-Cb5qGZIp.js` 数据（那是子站构建产物，直改等于替他的源码工作线做决定）。
