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

// 路由守卫把“页面权限”集中在一处管理，页面组件只需要关心自身展示和交互。
router.beforeEach(async (to) => {
  const authStore = useAuthStore();

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

  // 管理页不单独在组件里做判定，是因为权限控制越靠近路由入口越不容易漏掉。
  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    return { name: "workspace" };
  }

  return true;
});
