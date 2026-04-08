<script setup lang="ts">
defineProps<{
  title: string;
  subtitle: string;
  submitLabel: string;
  loading: boolean;
  errorMessage: string;
}>();

defineEmits<{
  (event: "submit"): void;
}>();

const username = defineModel<string>("username", { required: true });
const password = defineModel<string>("password", { required: true });
</script>

<template>
  <section class="auth-layout">
    <div class="auth-layout__intro">
      <p class="eyebrow">Document scanning studio</p>
      <h1>{{ title }}</h1>
      <p>{{ subtitle }}</p>
      <div class="auth-layout__glow" />
    </div>

    <form class="auth-card" @submit.prevent="$emit('submit')">
      <label class="field">
        <span>用户名</span>
        <input v-model="username" autocomplete="username" placeholder="例如：paperlover" required />
      </label>

      <label class="field">
        <span>密码</span>
        <input
          v-model="password"
          type="password"
          autocomplete="current-password"
          placeholder="至少 6 位"
          required
        />
      </label>

      <p v-if="errorMessage" class="inline-error">{{ errorMessage }}</p>
      <button class="primary-button" type="submit" :disabled="loading">
        {{ loading ? "提交中..." : submitLabel }}
      </button>
      <slot />
    </form>
  </section>
</template>
