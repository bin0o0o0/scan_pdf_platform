import { createRouter, createWebHistory } from "vue-router";

import { useAuthStore } from "../stores/auth";
import HomeView from "../views/HomeView.vue";
import LoginView from "../views/LoginView.vue";
import RegisterView from "../views/RegisterView.vue";
import WorkspaceView from "../views/WorkspaceView.vue";
import AccountView from "../views/AccountView.vue";
import UsersAdminView from "../views/admin/UsersAdminView.vue";

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "home", component: HomeView },
    { path: "/login", name: "login", component: LoginView },
    { path: "/register", name: "register", component: RegisterView },
    {
      path: "/workspace",
      name: "workspace",
      component: WorkspaceView,
      meta: { requiresAuth: true }
    },
    {
      path: "/account",
      name: "account",
      component: AccountView,
      meta: { requiresAuth: true }
    },
    {
      path: "/admin/users",
      name: "admin-users",
      component: UsersAdminView,
      meta: { requiresAuth: true, requiresAdmin: true }
    }
  ]
});

// 路由守卫可以理解成“进入页面之前的统一门禁”。
// 这样权限控制只写一处，页面组件本身就能更专注于展示和交互。
router.beforeEach(async (to) => {
  const authStore = useAuthStore();

  // 页面刷新后，Pinia 的内存状态会丢失，但 sessionStorage 里的 token 还在。
  // 所以这里要主动调用 /me，把当前用户资料重新拉回来。
  if (authStore.token && !authStore.currentUser && !authStore.isBootstrapping) {
    try {
      await authStore.bootstrap();
    } catch {
      return { name: "login" };
    }
  }

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return { name: "login", query: { redirect: to.fullPath } };
  }

  // 管理员页在路由入口就做拦截，比等组件加载后再判断更稳妥。
  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    return { name: "workspace" };
  }

  return true;
});
