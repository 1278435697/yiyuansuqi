import { createServer } from 'node:http';
import { existsSync, readFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { inflateRawSync } from 'node:zlib';

const ROOT = dirname(fileURLToPath(import.meta.url));

// 读取 apps/server/.env（存在才读），避免额外依赖
const envPath = resolve(ROOT, '.env');
if (existsSync(envPath)) {
  for (const line of readFileSync(envPath, 'utf8').split(/\r?\n/)) {
    const match = line.match(/^\s*([A-Za-z0-9_]+)\s*=\s*(.*)\s*$/);
    if (match && !process.env[match[1]]) {
      process.env[match[1]] = match[2].replace(/^["']|["']$/g, '');
    }
  }
}

const PORT = Number(process.env.PORT ?? 8787);
const ARK_BASE = (process.env.ARK_BASE_URL ?? 'https://ark.cn-beijing.volces.com/api/v3').replace(/\/$/, '');
const API_KEY = process.env.ARK_API_KEY ?? '';
const IMAGE_MODEL = process.env.ARK_IMAGE_MODEL ?? 'doubao-seedream-5-0-flash-260915';
/** 出图分辨率：2K（约 ¥0.12/张）或 4K（约 ¥0.25/张，脸部细节更清晰） */
const IMAGE_SIZE = process.env.ARK_IMAGE_SIZE ?? '2K';
/** 生成式 3D 供应商：off / tripo / hunyuan / hitem3d；默认关闭，避免误触发付费任务 */
const MODEL3D_PROVIDER = (process.env.MODEL3D_PROVIDER ?? 'off').toLowerCase();

/** 火山方舟 HiTem3D：面数越高越贵（1M 面约 ¥10/次） */
const MODEL3D = process.env.ARK_3D_MODEL ?? 'hitem3d-2-0-251223';
const MODEL3D_FACE = process.env.ARK_3D_FACE ?? '1000000';
const MODEL3D_RESOLUTION = process.env.ARK_3D_RESOLUTION ?? '1536';

/** Tripo H 系列：8K 贴图 50 积分（¥3.5），Ultra 几何 +20 积分（¥1.4） */
const TRIPO_KEY = process.env.TRIPO_API_KEY ?? '';
const TRIPO_BASE = (process.env.TRIPO_BASE_URL ?? 'https://openapi.tripo3d.com/v3').replace(/\/$/, '');
const TRIPO_MODEL = process.env.TRIPO_MODEL ?? 'v3.1-20260211';
const TRIPO_TEXTURE_QUALITY = process.env.TRIPO_TEXTURE_QUALITY ?? 'detailed';
const TRIPO_GEOMETRY_QUALITY = process.env.TRIPO_GEOMETRY_QUALITY ?? 'standard';
const TRIPO_FACE_LIMIT = Number(process.env.TRIPO_FACE_LIMIT ?? 0);
/** 跳过侧面输入：只喂正面+背面，避免侧面图与正面的脸/帽子冲突污染脸部贴图 */
const TRIPO_SKIP_SIDE = /^(1|true|yes)$/i.test(process.env.TRIPO_SKIP_SIDE ?? '');

/** 腾讯混元生3D（专业版）：带 PBR 与多视图约 40 积分（约 ¥2.4）/次 */
const HUNYUAN_KEY = process.env.HUNYUAN_API_KEY ?? '';
const HUNYUAN_BASE = (process.env.HUNYUAN_BASE_URL ?? 'https://api.ai3d.cloud.tencent.com').replace(/\/$/, '');
const HUNYUAN_MODEL = process.env.HUNYUAN_MODEL ?? '3.0';
const HUNYUAN_FACE = Number(process.env.HUNYUAN_FACE ?? 500000);
/** TokenHub 迁移后的接口使用 snake_case 与 Bearer 鉴权 */
const HUNYUAN_TOKENHUB = /tokenhub/i.test(HUNYUAN_BASE);

const FORCE_MOCK = process.env.ARK_MOCK === '1';
const MOCK = !API_KEY || FORCE_MOCK;

const GARMENT_RULE =
  '只提取图2中服装的款式、颜色、纹样、配饰和材质，忽略图2里的人台、模特、人脸、身体、姿势和背景；' +
  '如果图2包含帽子、发冠、披帛、腰带等服饰配件，则保留并穿戴到图1人物身上。';

const TRYON_PROMPT =
  '图1是人物照片，图2是服装参考。让图1中的人物换上图2的服装：' +
  GARMENT_RULE +
  '保持图1人物的脸型、五官、发型、肤色、身高和身材比例完全不变，不要换脸、不要改变表情；' +
  '严格正面 0° 视角：人物正对镜头，双肩水平，鼻尖朝镜头，双脚并拢朝前，双臂自然下垂；' +
  '纯中灰色背景（#B9BEC4，无渐变、无纹理），地面与背景同色且不产生人物阴影，均匀柔光，' +
  '全身完整入镜，头顶与脚底各留少量余量，不要裁切，不要出现文字、水印或边框。';

const KEEP_PROMPT =
  '保持图1中人物的脸型、五官、发型、肤色、身材比例和站姿完全不变，输出严格正面 0° 的全身站立照；' +
  '人物正对镜头，双肩水平，鼻尖朝镜头，双脚并拢朝前，双臂自然下垂；' +
  '纯中灰色背景（无渐变、无纹理），地面与背景同色且不产生人物阴影，均匀柔光，' +
  '全身完整入镜，头顶与脚底各留少量余量，不要裁切，不要出现文字、水印或边框。';

const VIEW_STYLE =
  '纯中灰色背景（#B9BEC4，无渐变、无纹理），地面与背景同色、人物脚下不产生投影，均匀柔光，' +
  '全身完整入镜，头顶与脚底各留少量余量，人物高度占画面约九成，不要裁切，不要文字或水印；' +
  '三张图必须是同一人物、同一服装、同一身高比例、同一背景、同一光照、同一相机高度，' +
  '不要改变姿势、衣长、袖型或鞋履。';

/** 三视图换衣：先生成正面作为锚点，侧面与背面都以它为比例/服装基准，降低三张图的漂移 */
const VIEW_PROMPTS = {
  front:
    '图1是人物正面照，图2是服装参考。让图1人物穿上图2的服装：' +
    GARMENT_RULE +
    '保持脸型、五官、发型、肤色、身高和身材比例完全不变；' +
    '严格正面 0° 视角：人物正对镜头，双肩水平，鼻尖朝镜头，双脚并拢朝前，双臂自然下垂；' +
    VIEW_STYLE,
  side:
    '图1是人物侧面照，图2是服装参考，图3是已换好同款服装的正面全身照。' +
    '生成同一人物穿图2服装的严格 90° 正侧视全身照：人物面朝画面右侧，' +
    '鼻尖、下巴、胸、腹、膝、脚踝的侧轮廓在同一垂直平面，不要 3/4 侧、不要回头、不要侧身；' +
    '靠近镜头的手臂自然下垂，不遮挡躯干和裙摆轮廓；' +
    '帽子/头饰的形状、颜色、高度、横簪与额饰必须与图3完全一致，绝对不能换成其它帽型；发型、鬓角长度也保持一致；' +
    '只改变拍摄角度，脸型、发型、身高体重比例、站姿、衣长、开衩高度、袖型、鞋履必须与图3完全一致；' +
    VIEW_STYLE,
  back:
    '图1是人物背面照，图2是服装参考，图3是已换好同款服装的正面全身照。' +
    '生成同一人物穿图2服装的严格 180° 正背视全身照：后脑、后颈、肩胛、腰、臀、裙摆、脚后跟完整可见；' +
    '不要侧身、不要回头、不要转身；' +
    '帽子/头饰的轮廓、高度、横簪必须与图3一致；后脑发型、发长、肤色也保持一致；' +
    '只改变拍摄角度，发型、身高体重比例、站姿、衣长、开衩高度、袖型、鞋履必须与图3完全一致；' +
    VIEW_STYLE,
};

/** 侧面二次对齐：只重绘帽子和头型，避免与正面的帽型冲突把 3D 头部带歪 */
const SIDE_ALIGN_PROMPT =
  '图1是侧面全身换装照，图2是服装参考，图3是正面成品。' +
  '只修正图1的帽子：把帽子改成与图3完全相同的黑色高冠——方形冠体、纵向褶皱、顶部横向长簪、额前青玉饰，' +
  '帽子的高度、宽度、轮廓与图3一致；不要添加飘带、缨络、帽翅或其它装饰；' +
  '图1中的人物脸型、五官、发型、肤色、姿势、手臂位置、服装、背景、光照、构图全部保持不变，' +
  '不要改变拍摄角度，不要重新生成人物，不要移动画面中的任何其它元素。';

/** 纯文字描述换装时没有服装参考图，二次对齐只用正面成品当帽型基准 */
const SIDE_ALIGN_CUSTOM_PROMPT = SIDE_ALIGN_PROMPT.replace('图2是服装参考，图3是正面成品', '图2是正面成品')
  .replaceAll('图3', '图2');

/** 纯文字描述换装：没有服装参考图，服装细节全部来自用户描述 */
function customTryonPrompt(view, description) {
  const garment = `服装为：${description}。只按这段描述决定服装的款式、颜色、纹样、配饰和材质，不要出现描述之外的服饰元素；`;
  if (view === 'front') {
    return (
      '图1是人物正面照，让图1人物换上这套服装。' +
      garment +
      '保持图1人物的脸型、五官、发型、肤色、身高和身材比例完全不变，不要换脸、不要改变表情；' +
      '严格正面 0° 视角：人物正对镜头，双肩水平，鼻尖朝镜头，双脚并拢朝前，双臂自然下垂；' +
      VIEW_STYLE
    );
  }
  const angle =
    view === 'side'
      ? '生成同一人物穿同一套服装的严格 90° 正侧视全身照：人物面朝画面右侧，' +
        '鼻尖、下巴、胸、腹、膝、脚踝的侧轮廓在同一垂直平面，不要 3/4 侧、不要回头、不要侧身；' +
        '靠近镜头的手臂自然下垂，不遮挡躯干和裙摆轮廓；'
      : '生成同一人物穿同一套服装的严格 180° 正背视全身照：后脑、后颈、肩胛、腰、臀、裙摆、脚后跟完整可见；' +
        '不要侧身、不要回头、不要转身；';
  return (
    `图1是人物${view === 'side' ? '侧面' : '背面'}照，图2是已换好同一套服装的正面全身照。` +
    garment +
    angle +
    '帽子/头饰的形状、颜色、高度必须与图2完全一致，绝对不能换成其它帽型；发型、鬓角长度也保持一致；' +
    '只改变拍摄角度，脸型、发型、身高体重比例、站姿、衣长、袖型、鞋履必须与图2完全一致；' +
    VIEW_STYLE
  );
}

/** mock / 真实任务统一存在内存里 */
const tasks = new Map();
/** 解压后的 GLB 缓存，避免重复下载同一个任务的文件 */
const modelFiles = new Map();

function sendJson(res, status, body) {
  const payload = JSON.stringify(body);
  res.writeHead(status, {
    'content-type': 'application/json; charset=utf-8',
    'access-control-allow-origin': '*',
    'cache-control': 'no-store',
  });
  res.end(payload);
}

async function readJson(req, limit = 40 * 1024 * 1024) {
  let size = 0;
  const chunks = [];
  for await (const chunk of req) {
    size += chunk.length;
    if (size > limit) throw new Error('请求体过大，请压缩照片后重试');
    chunks.push(chunk);
  }
  if (chunks.length === 0) return {};
  return JSON.parse(Buffer.concat(chunks).toString('utf8'));
}

async function arkJson(path, init) {
  const response = await fetch(`${ARK_BASE}${path}`, {
    ...init,
    headers: {
      authorization: `Bearer ${API_KEY}`,
      'content-type': 'application/json',
      ...(init?.headers ?? {}),
    },
  });
  const text = await response.text();
  let data;
  try {
    data = JSON.parse(text);
  } catch {
    data = null;
  }
  if (!response.ok) {
    const code = data?.error?.code ?? '';
    let modelName = '';
    try {
      modelName = JSON.parse(init?.body ?? '{}')?.model ?? '';
    } catch {
      /* body 不是 JSON 时忽略 */
    }
    if (code === 'ModelNotOpen') {
      throw new Error(`模型 ${modelName} 未开通，请在火山方舟控制台「开通管理」中启用`);
    }
    if (code === 'SetLimitExceeded') {
      throw new Error(
        `模型 ${modelName} 已达到「安全体验模式」用量上限，请在方舟控制台调整或关闭该模式后重试`,
      );
    }
    if (code === 'InvalidEndpointOrModel.NotFound') {
      throw new Error(`模型 ${modelName} 不存在或当前账号无权访问`);
    }
    const detail = data?.error?.message ?? data?.message ?? text.slice(0, 300);
    throw new Error(`方舟接口 ${response.status}：${detail}`);
  }
  return data;
}

/** Tripo 请求：统一带 Bearer Key，code 非 0 视为失败 */
async function tripoJson(path, init) {
  const response = await fetch(`${TRIPO_BASE}${path}`, {
    ...init,
    headers: {
      authorization: `Bearer ${TRIPO_KEY}`,
      'content-type': 'application/json',
      ...(init?.headers ?? {}),
    },
  });
  const text = await response.text();
  let data;
  try {
    data = JSON.parse(text);
  } catch {
    data = null;
  }
  if (!response.ok) {
    throw new Error(`Tripo 接口 ${response.status}：${data?.message ?? text.slice(0, 200)}`);
  }
  if (data?.code !== undefined && data.code !== 0) {
    throw new Error(`Tripo ${data.code}：${data.message ?? data.msg ?? '请求失败'}`);
  }
  return data;
}

/** 混元生3D 请求：兼容 ai3d.cloud（Authorization: sk-…）与 TokenHub（Bearer）两种鉴权 */
async function hunyuanJson(path, body) {
  const response = await fetch(`${HUNYUAN_BASE}${path}`, {
    method: 'POST',
    headers: {
      authorization: HUNYUAN_TOKENHUB ? `Bearer ${HUNYUAN_KEY}` : HUNYUAN_KEY,
      'content-type': 'application/json',
    },
    body: JSON.stringify(body),
  });
  const text = await response.text();
  let data;
  try {
    data = JSON.parse(text);
  } catch {
    data = null;
  }
  if (!response.ok) {
    throw new Error(`混元生3D 接口 ${response.status}：${data?.error?.message ?? text.slice(0, 200)}`);
  }
  const payload = data?.Response ?? data;
  if (payload?.Error?.Code) throw new Error(`混元生3D ${payload.Error.Code}：${payload.Error.Message ?? '请求失败'}`);
  if (payload?.error?.code) throw new Error(`混元生3D ${payload.error.code}：${payload.error.message ?? '请求失败'}`);
  return payload;
}

/** 从 3D 任务返回里尽力找模型文件地址，兼容不同字段命名 */
function extractModelUrl(node) {
  if (!node || typeof node !== 'object') return null;
  for (const [key, value] of Object.entries(node)) {
    if (typeof value === 'string' && /^https?:\/\//.test(value)) {
      if (/(\.glb|\.gltf|\.obj|\.fbx|model|file|asset)/i.test(key) || /\.(glb|gltf|obj|fbx)(\?|$)/i.test(value)) {
        return value;
      }
    }
    if (value && typeof value === 'object') {
      const found = extractModelUrl(value);
      if (found) return found;
    }
  }
  return null;
}

async function createTryonImage(person, outfit, description = '') {
  const images = description ? [person] : outfit ? [person, outfit] : [person];
  const prompt = description
    ? customTryonPrompt('front', description)
    : outfit
      ? TRYON_PROMPT
      : KEEP_PROMPT;
  const data = await arkJson('/images/generations', {
    method: 'POST',
    body: JSON.stringify({
      model: IMAGE_MODEL,
      prompt,
      image: images,
      size: IMAGE_SIZE,
      response_format: 'url',
      watermark: false,
    }),
  });
  const item = data?.data?.[0];
  const image = item?.url ?? (item?.b64_json ? `data:image/png;base64,${item.b64_json}` : null);
  if (!image) throw new Error('换衣接口未返回图片');
  return image;
}

async function createTryonView(view, person, outfit, anchor, description) {
  // 有文字描述时不再传服装参考图，正面成品的图序也随之前移
  const images = description
    ? anchor
      ? [person, anchor]
      : [person]
    : anchor
      ? [person, outfit, anchor]
      : [person, outfit];
  const data = await arkJson('/images/generations', {
    method: 'POST',
    body: JSON.stringify({
      model: IMAGE_MODEL,
      prompt: description ? customTryonPrompt(view, description) : VIEW_PROMPTS[view],
      image: images,
      size: IMAGE_SIZE,
      response_format: 'url',
      watermark: false,
    }),
  });
  const item = data?.data?.[0];
  const image = item?.url ?? (item?.b64_json ? `data:image/png;base64,${item.b64_json}` : null);
  if (!image) throw new Error(`${view} 视图未返回图片`);
  return image;
}

/**
 * 二次对齐：侧面图常把帽子/头饰画成另一种帽型，和正面对不上会把 3D 头型带歪。
 * 这里只重绘帽子，让它与正面成品一致，人物姿态、服装、背景保持不变。
 */
async function alignSideView(side, outfit, front, description) {
  const data = await arkJson('/images/generations', {
    method: 'POST',
    body: JSON.stringify({
      model: IMAGE_MODEL,
      prompt: description ? SIDE_ALIGN_CUSTOM_PROMPT : SIDE_ALIGN_PROMPT,
      image: description ? [side, front] : [side, outfit, front],
      size: IMAGE_SIZE,
      response_format: 'url',
      watermark: false,
    }),
  });
  const item = data?.data?.[0];
  const image = item?.url ?? (item?.b64_json ? `data:image/png;base64,${item.b64_json}` : null);
  if (!image) throw new Error('侧面二次对齐未返回图片');
  return image;
}

/** 解析 ZIP 中央目录，取出第一个 glb；方舟会把 3D 输出打包成 zip */
function glbFromZip(buffer) {
  const EOCD = 0x06054b50;
  let eocd = -1;
  const scanFrom = Math.max(0, buffer.length - 22 - 65535);
  for (let i = buffer.length - 22; i >= scanFrom; i--) {
    if (buffer.readUInt32LE(i) === EOCD) {
      eocd = i;
      break;
    }
  }
  if (eocd < 0) return null;

  const count = buffer.readUInt16LE(eocd + 10);
  let p = buffer.readUInt32LE(eocd + 16);
  for (let n = 0; n < count; n++) {
    if (p + 46 > buffer.length || buffer.readUInt32LE(p) !== 0x02014b50) return null;
    const method = buffer.readUInt16LE(p + 10);
    const compSize = buffer.readUInt32LE(p + 20);
    const fnLen = buffer.readUInt16LE(p + 28);
    const extraLen = buffer.readUInt16LE(p + 30);
    const commentLen = buffer.readUInt16LE(p + 32);
    const localOffset = buffer.readUInt32LE(p + 42);
    const name = buffer.toString('utf8', p + 46, p + 46 + fnLen);
    p += 46 + fnLen + extraLen + commentLen;

    if (!/\.(glb|gltf)$/i.test(name)) continue;
    if (localOffset + 30 > buffer.length || buffer.readUInt32LE(localOffset) !== 0x04034b50) return null;
    const localFn = buffer.readUInt16LE(localOffset + 26);
    const localExtra = buffer.readUInt16LE(localOffset + 28);
    const start = localOffset + 30 + localFn + localExtra;
    const packed = buffer.subarray(start, start + compSize);
    if (method === 0) return packed;
    if (method === 8) return inflateRawSync(packed);
    return null;
  }
  return null;
}

/** 任务成功后的文件可能是 zip，也可能直接是 glb，统一取出模型二进制 */
function modelFromArchive(buffer) {
  if (buffer.length >= 4 && buffer.toString('utf8', 0, 4) === 'glTF') return buffer;
  return glbFromZip(buffer);
}

/** Tripo 只接受公网 URL 或 file_token；历史三视图是 data URL，先上传换成 token */
async function tripoImage(value) {
  const match = /^data:([^;]+);base64,(.*)$/s.exec(value);
  if (!match) return value;

  const type = match[1] || 'image/png';
  const extension = /png/i.test(type) ? 'png' : 'jpg';
  const form = new FormData();
  form.append('file', new Blob([Buffer.from(match[2], 'base64')], { type }), `view.${extension}`);

  const response = await fetch(`${TRIPO_BASE}/files`, {
    method: 'POST',
    headers: { authorization: `Bearer ${TRIPO_KEY}` },
    body: form,
  });
  const text = await response.text();
  let data;
  try {
    data = JSON.parse(text);
  } catch {
    data = null;
  }
  const token = data?.data?.file_token;
  if (!response.ok || !token) {
    throw new Error(`Tripo 图片上传失败：${data?.message ?? text.slice(0, 200)}`);
  }
  return token;
}

/** Tripo：单图 image-to-model（正面换装照一张即出模），H 系列高精度 + 详细贴图 */
async function createTripoTask(image) {
  if (!TRIPO_KEY) throw new Error('未配置 TRIPO_API_KEY，请在 apps/server/.env 中填写');

  const input = await tripoImage(image);

  const payload = {
    input,
    model: TRIPO_MODEL,
    texture: true,
    pbr: true,
    texture_quality: TRIPO_TEXTURE_QUALITY,
    orientation: 'align_image',
    texture_alignment: 'original_image',
    // detailed = Ultra 几何，面数上限从 150 万提到 200 万
    geometry_quality: TRIPO_GEOMETRY_QUALITY,
  };
  if (Number.isFinite(TRIPO_FACE_LIMIT) && TRIPO_FACE_LIMIT > 0) {
    payload.face_limit = Math.min(2000000, TRIPO_FACE_LIMIT);
  }

  const data = await tripoJson('/generation/image-to-model', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  const id = data?.data?.task_id;
  if (!id) throw new Error('Tripo 未返回任务 id');
  tasks.set(id, { status: 'running', provider: 'tripo', createdAt: Date.now(), mock: false });
  return { id, mock: false, provider: 'tripo' };
}

/** 腾讯混元生3D：正面用主图，侧面/背面放进多视图参数 */
async function createHunyuanTask(list) {
  if (!HUNYUAN_KEY) throw new Error('未配置 HUNYUAN_API_KEY，请在 apps/server/.env 中填写');

  const multi = [];
  if (list[1]) multi.push({ type: 'right', image: list[1] });
  if (list[2]) multi.push({ type: 'back', image: list[2] });

  // data URL 只能走 Base64 字段；公网地址走 Url 字段，混元不接受 data URL 当普通链接
  const base64 = (value) => /^data:[^;]+;base64,(.*)$/s.exec(value)?.[1] ?? value;
  const inline = /^data:/i.test(list[0]);

  const body = HUNYUAN_TOKENHUB
    ? {
        model: `hy-3d-${HUNYUAN_MODEL}`,
        ...(inline ? { image_base64: base64(list[0]) } : { image_url: list[0] }),
        ...(multi.length
          ? {
              multi_view_images: multi.map((item) => ({
                view_type: item.type,
                ...(inline
                  ? { view_image_base64: base64(item.image) }
                  : { view_image_url: item.image }),
              })),
            }
          : {}),
        enable_pbr: true,
        generate_type: 'normal',
        ...(HUNYUAN_FACE > 0 ? { face_count: HUNYUAN_FACE } : {}),
      }
    : {
        Model: HUNYUAN_MODEL,
        ...(inline ? { ImageBase64: base64(list[0]) } : { ImageUrl: list[0] }),
        ...(multi.length
          ? {
              MultiViewImages: multi.map((item) => ({
                ViewType: item.type,
                ...(inline
                  ? { ViewImageBase64: base64(item.image) }
                  : { ViewImageUrl: item.image }),
              })),
            }
          : {}),
        EnablePBR: true,
        GenerateType: 'Normal',
        ...(HUNYUAN_FACE > 0 ? { FaceCount: HUNYUAN_FACE } : {}),
      };

  const path = HUNYUAN_TOKENHUB ? '/v1/api/3d/submit' : '/v1/ai3d/submit';
  const data = await hunyuanJson(path, body);
  const id = data?.JobId ?? data?.id;
  if (!id) throw new Error('混元生3D 未返回任务 id');
  tasks.set(String(id), { status: 'running', provider: 'hunyuan', createdAt: Date.now(), mock: false });
  return { id: String(id), mock: false, provider: 'hunyuan' };
}

/**
 * 火山方舟 HiTem3D 的多视图顺序固定为「前、后、左、右」，
 * 前端给的是「正面、侧面、背面」，这里重排成前/后/侧并用位图 1110 标记。
 */
async function createHitemTask(list) {
  if (!API_KEY) throw new Error('未配置 ARK_API_KEY，请在 apps/server/.env 中填写');

  let ordered = list;
  let bits = '';
  if (list.length === 3) {
    ordered = [list[0], list[2], list[1]];
    bits = '1110';
  } else if (list.length === 2) {
    bits = '1100';
  } else if (list.length === 1) {
    bits = '1000';
  }

  const command = `--resolution ${MODEL3D_RESOLUTION} --request_type 3 --ff 2 --face ${MODEL3D_FACE} --multi_images_bit ${bits}`;
  const content = [
    { type: 'text', text: command },
    ...ordered.map((image) => ({ type: 'image_url', image_url: { url: image } })),
  ];

  const data = await arkJson('/contents/generations/tasks', {
    method: 'POST',
    body: JSON.stringify({ model: MODEL3D, content }),
  });
  const id = data?.id;
  if (!id) throw new Error('3D 接口未返回任务 id');
  tasks.set(id, { status: 'running', provider: 'hitem3d', createdAt: Date.now(), mock: false });
  return { id, mock: false, provider: 'hitem3d' };
}

async function createModelTask(images) {
  const raw = (Array.isArray(images) ? images : [images]).filter(Boolean);
  if (raw.length === 0) throw new Error('缺少换衣后的图片');
  if (MODEL3D_PROVIDER === 'off') throw new Error('生成式 3D 已暂停');

  // 图生 3D：只吃正面这一张（多图 multiview 建模已停用）
  const single = raw[0];
  const list = [single];

  if (MOCK) {
    const id = `mock-${Date.now()}`;
    tasks.set(id, { status: 'running', createdAt: Date.now(), mock: true });
    setTimeout(() => {
      const task = tasks.get(id);
      if (task) tasks.set(id, { ...task, status: 'done', url: '/models/mock-person.glb' });
    }, 2200);
    return { id, mock: true };
  }

  if (MODEL3D_PROVIDER === 'tripo') return createTripoTask(single);
  if (MODEL3D_PROVIDER === 'hunyuan') return createHunyuanTask(list);
  if (MODEL3D_PROVIDER === 'hitem3d') return createHitemTask(list);
  throw new Error(`未知的 3D 供应商：${MODEL3D_PROVIDER}`);
}

/** 真实任务：每次查询都把方舟状态映射成前端可用的 pending/done/error */
function doneModelTask(id, cached, archive) {
  const url = `/api/3d/${encodeURIComponent(id)}/model`;
  tasks.set(id, { ...cached, status: 'done', archive, url });
  return { status: 'done', url };
}

async function pollTripoTask(id, cached) {
  const data = await tripoJson(`/tasks/${encodeURIComponent(id)}`);
  const task = data?.data ?? {};
  if (task.status === 'success') {
    const archive = task.output?.model_url ?? task.output?.pbr_model?.url;
    if (!archive) return { status: 'error', message: 'Tripo 任务成功但未返回模型地址' };
    return doneModelTask(id, cached, archive);
  }
  if (task.status === 'failed' || task.status === 'cancelled' || task.status === 'banned') {
    return { status: 'error', message: task.error?.message ?? `Tripo 任务${task.status}` };
  }
  return { status: 'running' };
}

async function pollHunyuanTask(id, cached) {
  const body = HUNYUAN_TOKENHUB
    ? { model: `hy-3d-${HUNYUAN_MODEL}`, id }
    : { JobId: id };
  const data = await hunyuanJson(HUNYUAN_TOKENHUB ? '/v1/api/3d/query' : '/v1/ai3d/query', body);
  const status = String(data?.status ?? data?.Status ?? '').toUpperCase();

  if (['COMPLETED', 'DONE', 'SUCCESS', 'SUCCEEDED'].includes(status)) {
    const files = data?.data ?? data?.ResultFile3Ds ?? [];
    const glb = files.find((file) => /glb/i.test(String(file?.type ?? file?.Type ?? ''))) ?? files[0];
    const archive = glb?.url ?? glb?.Url ?? extractModelUrl(files);
    if (!archive) return { status: 'error', message: '混元生3D 任务成功但未返回模型地址' };
    return doneModelTask(id, cached, archive);
  }
  if (['FAIL', 'FAILED', 'ERROR'].includes(status)) {
    return {
      status: 'error',
      message: data?.ErrorMessage ?? data?.error_message ?? data?.error?.message ?? '混元生3D 任务失败',
    };
  }
  return { status: 'running' };
}

async function pollHitemTask(id, cached) {
  const data = await arkJson(`/contents/generations/tasks/${encodeURIComponent(id)}`);
  const status = data?.status;
  if (status === 'succeeded') {
    // HiTem3D 把 GLB 打包成 zip 放在 content.file_url；Seed3D 走通用探测
    const archive = data?.content?.file_url ?? extractModelUrl(data);
    if (!archive) return { status: 'error', message: '任务成功但未找到模型文件地址' };
    return doneModelTask(id, cached, archive);
  }
  if (status === 'failed' || status === 'cancelled') {
    return { status: 'error', message: data?.error?.message ?? `任务${status}` };
  }
  return { status: 'running' };
}

async function pollModelTask(id) {
  const cached = tasks.get(id);
  if (!cached) return { status: 'error', message: '任务不存在或已过期' };
  if (cached.mock) {
    return { status: cached.status === 'done' ? 'done' : 'running', url: cached.url, mock: true };
  }
  if (cached.provider === 'tripo') return pollTripoTask(id, cached);
  if (cached.provider === 'hunyuan') return pollHunyuanTask(id, cached);
  return pollHitemTask(id, cached);
}

const server = createServer(async (req, res) => {
  const url = new URL(req.url ?? '/', `http://127.0.0.1:${PORT}`);

  if (req.method === 'OPTIONS') {
    res.writeHead(204, {
      'access-control-allow-origin': '*',
      'access-control-allow-headers': 'content-type',
      'access-control-allow-methods': 'GET,POST,OPTIONS',
    });
    res.end();
    return;
  }

  try {
    if (url.pathname === '/api/health') {
      sendJson(res, 200, {
        ok: true,
        mode: MOCK ? 'mock' : 'ark',
        models: { image: IMAGE_MODEL, model3d: MODEL3D_PROVIDER },
      });
      return;
    }

    if (url.pathname === '/api/tryon' && req.method === 'POST') {
      const body = await readJson(req);
      if (!body.person) {
        sendJson(res, 400, { error: '缺少人物照片' });
        return;
      }
      const description = typeof body.prompt === 'string' ? body.prompt.trim().slice(0, 400) : '';
      if (MOCK) {
        sendJson(res, 200, { image: body.person, mock: true, mode: 'mock' });
        return;
      }
      const image = await createTryonImage(body.person, body.outfit, description);
      sendJson(res, 200, { image, mock: false, mode: 'ark' });
      return;
    }

    if (url.pathname === '/api/tryon-views' && req.method === 'POST') {
      const body = await readJson(req);
      const views = body.views ?? {};
      const description = typeof body.prompt === 'string' ? body.prompt.trim().slice(0, 400) : '';
      if (!views.front || !views.side || !views.back || (!body.outfit && !description)) {
        sendJson(res, 400, { error: '三视图换衣需要正面、侧面、背面照片，以及服饰参考图或服装描述' });
        return;
      }
      if (MOCK) {
        sendJson(res, 200, { images: [views.front, views.side, views.back], mock: true, mode: 'mock' });
        return;
      }
      const front = await createTryonView('front', views.front, body.outfit, null, description);
      const sideDraft = await createTryonView('side', views.side, body.outfit, front, description);
      const back = await createTryonView('back', views.back, body.outfit, front, description);
      let side = sideDraft;
      try {
        side = await alignSideView(sideDraft, body.outfit, front, description);
      } catch (error) {
        console.warn('[fitview] 侧面二次对齐失败，沿用原始侧面图', error);
      }
      sendJson(res, 200, { images: [front, side, back], mock: false, mode: 'ark' });
      return;
    }

    if (url.pathname === '/api/3d' && req.method === 'POST') {
      const body = await readJson(req);
      const images = body.images ?? (body.image ? [body.image] : []);
      if (images.length === 0) {
        sendJson(res, 400, { error: '缺少换衣后的图片' });
        return;
      }
      const task = await createModelTask(images);
      sendJson(res, 200, task);
      return;
    }

    if (url.pathname.startsWith('/api/3d/') && url.pathname.endsWith('/model') && req.method === 'GET') {
      const id = decodeURIComponent(url.pathname.slice('/api/3d/'.length, -'/model'.length));
      const cached = tasks.get(id);
      if (!cached || cached.status !== 'done' || !cached.archive) {
        sendJson(res, 404, { error: '模型尚未生成完成' });
        return;
      }
      let model = modelFiles.get(id);
      if (!model) {
        const upstream = await fetch(cached.archive);
        if (!upstream.ok) throw new Error(`下载模型失败（${upstream.status}）`);
        const buffer = Buffer.from(await upstream.arrayBuffer());
        const extracted = modelFromArchive(buffer);
        if (!extracted) throw new Error('模型压缩包中未找到 GLB 文件');
        model = Buffer.from(extracted);
        modelFiles.set(id, model);
      }
      res.writeHead(200, {
        'content-type': 'model/gltf-binary',
        'content-length': model.length,
        'access-control-allow-origin': '*',
        'cache-control': 'public, max-age=86400',
      });
      res.end(model);
      return;
    }

    if (url.pathname.startsWith('/api/3d/') && req.method === 'GET') {
      const id = decodeURIComponent(url.pathname.slice('/api/3d/'.length));
      sendJson(res, 200, await pollModelTask(id));
      return;
    }

    if (url.pathname === '/api/asset' && req.method === 'GET') {
      const target = url.searchParams.get('url') ?? '';
      if (!/^https:\/\//.test(target)) {
        sendJson(res, 400, { error: '仅支持 https 资源代理' });
        return;
      }
      const upstream = await fetch(target);
      const buffer = Buffer.from(await upstream.arrayBuffer());
      res.writeHead(upstream.status, {
        'content-type': upstream.headers.get('content-type') ?? 'application/octet-stream',
        'access-control-allow-origin': '*',
        'cache-control': 'public, max-age=3600',
      });
      res.end(buffer);
      return;
    }

    sendJson(res, 404, { error: '接口不存在' });
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    sendJson(res, 500, { error: message });
  }
});

server.listen(PORT, '127.0.0.1', () => {
  console.log(`[fitview] 代理已启动 http://127.0.0.1:${PORT}  模式=${MOCK ? 'mock（未配置 ARK_API_KEY）' : 'ark'}`);
  console.log(`[fitview] 换衣模型 ${IMAGE_MODEL} · 3D 供应商 ${MODEL3D_PROVIDER}`);
});
