import axios from "axios";

let authTokenGetter: (() => string | null) | null = null;

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:5000"
});

// 这里不直接 import auth store，是为了避免“API 模块依赖 store，store 又依赖 API”
// 这种循环依赖。改成由外部注册一个 getter，会更清晰也更安全。
export function setAuthTokenGetter(getter: () => string | null) {
  authTokenGetter = getter;
}

apiClient.interceptors.request.use((config) => {
  const token = authTokenGetter?.();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      return Promise.reject(new Error("登录已过期，请重新登录后再试。"));
    }

    const message = error?.response?.data?.message || error?.message || "请求失败，请稍后再试。";
    return Promise.reject(new Error(message));
  }
);
