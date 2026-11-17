/** 全站问答统一的「当前模型」记忆（localStorage），各入口共用同一个键 */
export const AI_MODEL_STORAGE_KEY = "yisu_ai_model";

export function aiModel(): string {
  try {
    return localStorage.getItem(AI_MODEL_STORAGE_KEY) || "";
  } catch {
    return "";
  }
}

export function setAiModel(id: string) {
  try {
    if (id) localStorage.setItem(AI_MODEL_STORAGE_KEY, id);
  } catch {
    /* 隐私模式忽略 */
  }
}

/** 后端 /api/aiqa/models 失败时的兜底清单（与后端内置清单一致） */
export const AI_MODEL_FALLBACK = [
  { id: "glm-4-flash", note: "轻量 · 最快" },
  { id: "glm-4.5-flash", note: "4.5 轻量 · 快" },
  { id: "glm-4.5-air", note: "4.5 均衡" },
  { id: "glm-4.5", note: "4.5 标准" },
  { id: "glm-4.6", note: "4.6 标准" },
  { id: "glm-4.7", note: "4.7 增强" },
  { id: "glm-5", note: "5 旗舰 · 稳但慢" },
  { id: "glm-5-turbo", note: "5 加速版" },
  { id: "glm-5.1", note: "5.1 旗舰" },
  { id: "glm-5.2", note: "5.2 旗舰" },
  { id: "glm-5.3", note: "5.3 最新旗舰" },
  { id: "glm-5.3-flash", note: "5.3 轻量 · 快" },
  { id: "glm-5.3-flashx", note: "5.3 加速旗舰" },
];
