import axios from "axios";
import { ElMessage } from "element-plus";

/** 类型化 HTTP 客户端：拦截器已解包 res.data */
export interface HttpClient {
  get<T = any>(url: string, config?: Record<string, any>): Promise<T>;
  post<T = any>(url: string, data?: any, config?: Record<string, any>): Promise<T>;
  put<T = any>(url: string, data?: any, config?: Record<string, any>): Promise<T>;
  delete<T = any>(url: string, config?: Record<string, any>): Promise<T>;
}

const instance = axios.create({
  // 开发模式直连后端（避开沙箱网络层对 vite 代理的劫持）；生产构建走同源 /api
  baseURL: import.meta.env.DEV ? "http://127.0.0.1:8765/api" : "/api",
  timeout: 30000,
});

instance.interceptors.request.use((config) => {
  const token = localStorage.getItem("yisu_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

instance.interceptors.response.use(
  (res) => res.data,
  (err) => {
    const msg = err?.response?.data?.detail || err?.message || "请求失败";
    if (err?.response?.status === 401) {
      localStorage.removeItem("yisu_token");
    }
    ElMessage.error(msg);
    return Promise.reject(err);
  },
);

const request = instance as unknown as HttpClient;
export default request;
