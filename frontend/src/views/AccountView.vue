<script setup lang="ts">
import { ref } from "vue";

import AppShell from "../components/AppShell.vue";
import { useAuthStore } from "../stores/auth";

const authStore = useAuthStore();

const oldPassword = ref("");
const newPassword = ref("");
const message = ref("");
const errorMessage = ref("");
const isSubmitting = ref(false);

async function handleSubmit() {
  isSubmitting.value = true;
  message.value = "";
  errorMessage.value = "";

  try {
    const response = await authStore.changePassword(oldPassword.value, newPassword.value);
    message.value = response.message;
    oldPassword.value = "";
    newPassword.value = "";
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "修改失败。";
  } finally {
    isSubmitting.value = false;
  }
}
</script>

<template>
  <AppShell
    title="账户设置"
    description="账户页只保留当前 V1 范围需要的能力：查看基础信息与修改密码，避免把页面做成杂糅的个人中心。"
  >
    <div class="workspace-grid workspace-grid--account">
      <section class="panel">
        <p class="eyebrow">Profile</p>
        <h2>基础信息</h2>
        <dl class="account-list">
          <div>
            <dt>用户名</dt>
            <dd>{{ authStore.currentUser?.username }}</dd>
          </div>
          <div>
            <dt>角色</dt>
            <dd>{{ authStore.currentUser?.role }}</dd>
          </div>
          <div>
            <dt>状态</dt>
            <dd>{{ authStore.currentUser?.status }}</dd>
          </div>
        </dl>
      </section>

      <section class="panel">
        <p class="eyebrow">Security</p>
        <h2>修改密码</h2>
        <form class="stack-form" @submit.prevent="handleSubmit">
          <label class="field">
            <span>旧密码</span>
            <input v-model="oldPassword" type="password" required />
          </label>
          <label class="field">
            <span>新密码</span>
            <input v-model="newPassword" type="password" required />
          </label>
          <p v-if="message" class="inline-success">{{ message }}</p>
          <p v-if="errorMessage" class="inline-error">{{ errorMessage }}</p>
          <button class="primary-button" type="submit" :disabled="isSubmitting">
            {{ isSubmitting ? "提交中..." : "更新密码" }}
          </button>
        </form>
      </section>
    </div>
  </AppShell>
</template>
