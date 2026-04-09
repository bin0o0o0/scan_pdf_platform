<script setup lang="ts">
import BrandMark from "./BrandMark.vue";
import { useAuthStore } from "../stores/auth";

defineProps<{
  title: string;
  description: string;
}>();

const authStore = useAuthStore();

async function handleLogout() {
  authStore.logout();

  // 这里用 location.assign 做一次“硬跳转”，
  // 可以把当前页内存状态一并清掉，适合教学项目演示完整退出效果。
  await window.location.assign("/login");
}
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <RouterLink to="/" class="topbar__brand">
        <BrandMark />
      </RouterLink>

      <nav class="topbar__nav">
        <RouterLink to="/workspace">工作台</RouterLink>
        <RouterLink to="/account">账户</RouterLink>
        <RouterLink v-if="authStore.isAdmin" to="/admin/users">用户管理</RouterLink>
        <button class="ghost-button" @click="handleLogout">退出</button>
      </nav>
    </header>

    <main class="app-main">
      <section class="page-heading">
        <div>
          <p class="eyebrow">Authenticated workspace</p>
          <h1>{{ title }}</h1>
        </div>
        <p>{{ description }}</p>
      </section>

      <slot />
    </main>
  </div>
</template>
