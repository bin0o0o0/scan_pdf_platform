<script setup lang="ts">
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import AuthCard from "../components/AuthCard.vue";
import { useAuthStore } from "../stores/auth";

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();

const username = ref("");
const password = ref("");
const errorMessage = ref("");
const isLoading = ref(false);

async function handleSubmit() {
  isLoading.value = true;
  errorMessage.value = "";

  try {
    await authStore.login(username.value, password.value);
    await authStore.refreshCurrentUser();
    const redirect = typeof route.query.redirect === "string" ? route.query.redirect : "/workspace";
    await router.push(redirect);
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "登录失败。";
  } finally {
    isLoading.value = false;
  }
}
</script>

<template>
  <AuthCard
    v-model:username="username"
    v-model:password="password"
    title="登录后开始整理你的文档。"
    subtitle="这里保留首页的气质，但把注意力收束到登录动作本身。"
    submit-label="登录"
    :loading="isLoading"
    :error-message="errorMessage"
    @submit="handleSubmit"
  >
    <p class="auth-card__footer">
      还没有账号？
      <RouterLink to="/register">去注册</RouterLink>
    </p>
  </AuthCard>
</template>
