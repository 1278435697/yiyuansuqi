/** 衣溯 · 华夏衣冠志 · 九大模块 API 封装 */

import request from "./request";

/* ---------- 模块8 · 用户 ---------- */
export const login = (username: string, password: string) =>
  request.post("/user/login", { username, password });
export const register = (username: string, password: string, email: string) =>
  request.post("/user/register", { username, password, email });
export const fetchMe = () => request.get("/user/me");
export const fetchMyLogs = () => request.get("/user/me/logs");
export const fetchMyStats = () => request.get("/user/me/stats");
export const updateAvatar = (avatar: string) => request.post("/user/me/avatar", { avatar });
export const updateUsername = (username: string) => request.post("/user/me/username", { username });

/** 上传图片到服务器存储，返回可访问 URL（部署到云服务器即云端） */
export async function uploadImage(file: File): Promise<string> {
  const form = new FormData();
  form.append("file", file);
  const res: any = await request.post("/upload/image", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.url;
}
export const fetchMyCollections = () => request.get("/user/me/collections");
export const adminDeletePost = (postId: number) => request.post(`/user/admin/audit/posts/${postId}/delete`);
export const fetchAuditPosts = () => request.get("/user/admin/audit/posts");
export const fetchMyDrafts = () => request.get("/user/me/drafts");
export const fetchMyWorks = () => request.get("/user/me/works");
export const fetchMyPosts = () => request.get("/user/me/posts");
export const fetchMyQuestions = () => request.get("/user/me/questions");

/* ---------- 模块1 · 文博资讯首页 ---------- */
export const fetchNews = (params: Record<string, any>) => request.get("/home/news", { params });
export const fetchNewsDetail = (id: number) => request.get(`/home/news/${id}`);
export const fetchHotTags = () => request.get("/home/hot-tags");
export const fetchTrendKeywords = () => request.get("/home/trend-keywords");
export const fetchCostumeLinks = () => request.get("/home/costume-links");
export const fetchWebSearch = (params: Record<string, any>) => request.get("/home/news-search", { params });

/* ---------- 模块2 · 服饰档案 + 第一人称对话 ---------- */
export const fetchCostumes = (params: Record<string, any>) => request.get("/archive/costumes", { params });
export const fetchCostumeDetail = (id: number) => request.get(`/archive/costumes/${id}`);
export const fetchArchiveWebSearch = (query: string) => request.get("/archive/web-search", { params: { q: query, n: 8 } });
export const fetchEras = () => request.get("/archive/eras");
export const createCostume = (data: Record<string, any>) => request.post("/archive/costumes", data);
export const deleteCostume = (id: number) => request.delete(`/archive/costumes/${id}`);

/* ---------- 服装面料版块 ---------- */
export const fetchFabrics = (category = "") =>
  request.get("/fabrics/list", { params: { category: category || undefined } });
export const fetchFabricWebSearch = (query: string) =>
  request.get("/fabrics/web-search", { params: { q: query, n: 8 } });
export const createFabric = (data: Record<string, any>) => request.post("/fabrics", data);
export const deleteFabric = (id: number) => request.delete(`/fabrics/${id}`);
export const chatWithCostume = (costumeId: number, message: string) =>
  request.post("/archive/chat", { costume_id: costumeId, message });

/* ---------- 模块3 · 千年衣脉时间轴 ---------- */
export const fetchTimeline = () => request.get("/timeline/timeline");
export const fetchTimelineDetail = (dynasty: string) => request.get(`/timeline/timeline/${dynasty}`);

/* ---------- 模块4 · 出土地理热力图 ---------- */
export const fetchRelics = (params: Record<string, any>) => request.get("/geomap/relics", { params });
export const fetchGeoStats = () => request.get("/geomap/geo-stats");
export const fetchMapConfig = () => request.get("/geomap/map-config");

/* ---------- 模块6 · AI 溯源问答 ---------- */
export const createQuestion = (body: Record<string, any>) => request.post("/aiqa/questions", body);
export const fetchAiChat = (body: Record<string, any>) => request.post("/aiqa/chat", body);
export const fetchAiRecommend = (params: Record<string, any>) => request.get("/aiqa/recommend", { params });
export const fetchQuestions = (params: Record<string, any>) => request.get("/aiqa/questions", { params });
export const fetchQuestionDetail = (id: number) => request.get(`/aiqa/questions/${id}`);
export const questionToPost = (id: number) => request.post(`/aiqa/questions/${id}/to_post`);
export const deleteQuestion = (id: number) => request.delete(`/aiqa/questions/${id}`);
export const addAnswer = (qid: number, content: string) =>
  request.post(`/aiqa/questions/${qid}/answers`, { content });
export const aiVerifyAnswer = (aid: number) => request.post(`/aiqa/answers/${aid}/verify`);

/* ---------- 模块7 · 社区 ---------- */
export const fetchBoards = () => request.get("/community/boards");
export const fetchPosts = (params: Record<string, any>) => request.get("/community/posts", { params });
export const fetchPostDetail = (id: number) => request.get(`/community/posts/${id}`);
export const fetchMyInteractions = () => request.get("/community/my/interactions");
export const createPost = (body: Record<string, any>) => request.post("/community/posts", body);
export const deletePost = (postId: number) => request.delete(`/community/posts/${postId}`);
export const createReply = (postId: number, content: string, parentReplyId?: number) =>
  request.post(`/community/posts/${postId}/replies`, { content, parent_reply_id: parentReplyId });
export const toggleLike = (postId: number) => request.post(`/community/posts/${postId}/like`);
export const toggleCollect = (postId: number, folderName?: string) =>
  request.post(`/community/posts/${postId}/collect`, null, { params: { folder_name: folderName } });
export const repost = (postId: number, comment?: string) =>
  request.post(`/community/posts/${postId}/repost`, { comment });
export const onlinePost = (postId: number) => request.post(`/community/posts/${postId}/online`);
export const offlinePost = (postId: number) => request.post(`/community/posts/${postId}/offline`);
export const pinPost = (postId: number) => request.post(`/community/posts/${postId}/pin`);
export const unpinPost = (postId: number) => request.post(`/community/posts/${postId}/unpin`);
export const applyOnline = (postId: number) => request.post(`/community/posts/${postId}/apply-online`);

/* ---------- 纹样资料库 ---------- */
export const fetchPatternCategories = () => request.get("/pattern-library/categories");
export const fetchPatternItems = (params: Record<string, any>) => request.get("/pattern-library/items", { params });
export const fetchPatternDetail = (id: number) => request.get(`/pattern-library/${id}`);
export const createPattern = (data: Record<string, any>) => request.post("/pattern-library", data);
export const deletePattern = (id: number) => request.delete(`/pattern-library/${id}`);

/* ---------- 模块9 · 文化传承生成 ---------- */
export const fetchHeritageProfile = () => request.get("/heritage/profile");
export const generatePlan = () => request.post("/heritage/generate-plan");
export const generateCard = (body: Record<string, any>) => request.post("/heritage/generate-card", body);
export const generateCommitment = () => request.post("/heritage/commitment");

/* ---------- 时空推演模拟器 ---------- */
export const fetchSimulatorEras = () => request.get("/simulator/eras");
export const simulateEra = (eraIdx: number, params: Record<string, number>) =>
  request.post("/simulator/simulate", { era_idx: eraIdx, params });
export const fetchSimulatorTrend = (params: Record<string, number>) =>
  request.post("/simulator/trend", { params });
