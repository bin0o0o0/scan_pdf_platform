<script setup lang="ts">
import type { User, UserRole, UserStatus } from "../types";

defineProps<{
  users: User[];
  loading: boolean;
}>();

defineEmits<{
  (event: "change-role", userId: number, role: UserRole): void;
  (event: "change-status", userId: number, status: UserStatus): void;
}>();
</script>

<template>
  <div class="table-panel">
    <table class="data-table">
      <thead>
        <tr>
          <th>用户名</th>
          <th>角色</th>
          <th>状态</th>
          <th>创建时间</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="user in users" :key="user.id">
          <td>{{ user.username }}</td>
          <td>
            <span class="pill">{{ user.role }}</span>
          </td>
          <td>
            <span class="pill" :class="{ 'pill--warn': user.status === 'disabled' }">{{ user.status }}</span>
          </td>
          <td>{{ user.created_at ? new Date(user.created_at).toLocaleString() : "-" }}</td>
          <td class="table-actions">
            <button
              class="ghost-button"
              @click="$emit('change-role', user.id, user.role === 'admin' ? 'user' : 'admin')"
            >
              切换角色
            </button>
            <button
              class="ghost-button"
              @click="$emit('change-status', user.id, user.status === 'active' ? 'disabled' : 'active')"
            >
              {{ user.status === "active" ? "禁用" : "启用" }}
            </button>
          </td>
        </tr>
        <tr v-if="!users.length && !loading">
          <td colspan="5" class="empty-cell">暂时没有用户数据。</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
