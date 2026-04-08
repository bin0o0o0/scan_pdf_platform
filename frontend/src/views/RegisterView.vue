<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";

import AuthCard from "../components/AuthCard.vue";
import { useAuthStore } from "../stores/auth";

const router = useRouter();
const authStore = useAuthStore();

const username = ref("");
const password = ref("");
const errorMessage = ref("");
const isLoading = ref(false);

async function handleSubmit() {
  isLoading.value = true;
  errorMessage.value = "";

  try {
    await authStore.register(username.value, password.value);
    await authStore.login(username.value, password.value);
    await router.push("/workspace");
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "注册失败。";
  } finally {
    isLoading.value = false;
  }
}
</script>

<template>
  <AuthCard
    v-model:username="username"
    v-model:password="password"
    title="创建账号，开始你的扫描工作台。"
    subtitle="注册完成后会直接登录，方便立刻进入工作区体验完整流程。"
    submit-label="注册并进入"
    :loading="isLoading"
    :error-message="errorMessage"
    @submit="handleSubmit"
  >
    <p class="auth-card__footer">
      已经有账号？
      <RouterLink to="/login">去登录</RouterLink>
    </p>
  </AuthCard>
</template>
