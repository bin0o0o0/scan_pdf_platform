<script setup lang="ts">
import { onMounted, ref } from "vue";

import AppShell from "../../components/AppShell.vue";
import UserAdminTable from "../../components/UserAdminTable.vue";
import { changeUserRole, changeUserStatus, fetchUsers } from "../../api/admin";
import type { User, UserRole, UserStatus } from "../../types";

const users = ref<User[]>([]);
const loading = ref(false);
const errorMessage = ref("");

async function loadUsers() {
  loading.value = true;
  errorMessage.value = "";

  try {
    users.value = await fetchUsers();
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "获取用户列表失败。";
  } finally {
    loading.value = false;
  }
}

async function handleRoleChange(userId: number, role: UserRole) {
  try {
    await changeUserRole(userId, role);
    await loadUsers();
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "更新角色失败。";
  }
}

async function handleStatusChange(userId: number, status: UserStatus) {
  try {
    await changeUserStatus(userId, status);
    await loadUsers();
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "更新状态失败。";
  }
}

onMounted(loadUsers);
</script>

<template>
  <AppShell
    title="用户管理"
    description="管理员页保持工具型布局：表格为主体，角色与状态操作直接贴近数据，不用花哨装饰分散注意力。"
  >
    <section class="panel">
      <div class="panel-heading">
        <div>
          <p class="eyebrow">Admin tools</p>
          <h2>用户列表</h2>
        </div>
        <button class="ghost-button" :disabled="loading" @click="loadUsers">刷新列表</button>
      </div>

      <p v-if="errorMessage" class="inline-error">{{ errorMessage }}</p>
      <UserAdminTable
        :users="users"
        :loading="loading"
        @change-role="handleRoleChange"
        @change-status="handleStatusChange"
      />
    </section>
  </AppShell>
</template>
