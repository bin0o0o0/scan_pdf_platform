import { computed, ref } from "vue";
import { defineStore } from "pinia";

import { fetchCurrentUser, loginAccount, registerAccount, updatePassword } from "../api/auth";
import { setAuthTokenGetter } from "../api/client";
import type { User } from "../types";

const TOKEN_KEY = "scan-pdf-token";

export const useAuthStore = defineStore("auth", () => {
  // token 持久化在 sessionStorage，浏览器标签页关闭后自动失效，
  // 对学习项目来说比 localStorage 更克制一些。
  const token = ref<string | null>(sessionStorage.getItem(TOKEN_KEY));
  const currentUser = ref<User | null>(null);
  const isBootstrapping = ref(false);

  // API 层不直接 import store，而是通过 getter 回调拿 token，
  // 这样可以避免“API 模块依赖 store，store 又依赖 API”的循环引用。
  setAuthTokenGetter(() => token.value);

  const isAuthenticated = computed(() => Boolean(token.value && currentUser.value));
  const isAdmin = computed(() => currentUser.value?.role === "admin");

  async function bootstrap() {
    if (!token.value) {
      return;
    }

    isBootstrapping.value = true;
    try {
      // 启动时重新请求 /me，是为了让前端状态以服务端的真实用户状态为准。
      currentUser.value = await fetchCurrentUser();
    } catch (error) {
      logout();
      throw error;
    } finally {
      isBootstrapping.value = false;
    }
  }

  async function login(username: string, password: string) {
    const response = await loginAccount(username, password);
    token.value = response.token;
    currentUser.value = response.user;
    sessionStorage.setItem(TOKEN_KEY, response.token);
  }

  async function register(username: string, password: string) {
    await registerAccount(username, password);
  }

  function logout() {
    token.value = null;
    currentUser.value = null;
    sessionStorage.removeItem(TOKEN_KEY);
  }

  async function refreshCurrentUser() {
    if (!token.value) {
      currentUser.value = null;
      return null;
    }

    currentUser.value = await fetchCurrentUser();
    return currentUser.value;
  }

  async function changePassword(oldPassword: string, newPassword: string) {
    return updatePassword(oldPassword, newPassword);
  }

  return {
    token,
    currentUser,
    isBootstrapping,
    isAuthenticated,
    isAdmin,
    bootstrap,
    login,
    register,
    logout,
    refreshCurrentUser,
    changePassword
  };
});
