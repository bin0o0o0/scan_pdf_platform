<script setup lang="ts">
import { computed } from "vue";

import AppShell from "../components/AppShell.vue";
import FileUploadPanel from "../components/FileUploadPanel.vue";
import { useAuthStore } from "../stores/auth";
import { useScanStore } from "../stores/scan";

const authStore = useAuthStore();
const scanStore = useScanStore();

const selectedFiles = computed(() => scanStore.selectedFiles);

function onFilesSelected(files: File[]) {
  scanStore.addFiles(files);
}

async function submitFiles() {
  if (!scanStore.selectedFiles.length) {
    scanStore.errorMessage = "请先选择至少一张图片。";
    return;
  }

  try {
    await scanStore.submitFiles();
  } catch {
    // 错误信息已经在 store 里统一处理，这里不重复覆盖。
  }
}
</script>

<template>
  <AppShell
    title="工作台"
    description="这里把上传、文件顺序、提交动作和结果下载收在同一屏，方便把前后端的扫描链路一次看清。"
  >
    <div class="workspace-grid">
      <section class="panel">
        <p class="eyebrow">Uploader</p>
        <h2>上传待扫描的图片</h2>
        <p>当前登录用户：{{ authStore.currentUser?.username }}</p>
        <FileUploadPanel @files-selected="onFilesSelected" />
      </section>

      <section class="panel">
        <p class="eyebrow">Queue</p>
        <h2>文件列表</h2>
        <ul class="file-list">
          <li v-for="(file, index) in selectedFiles" :key="`${file.name}-${index}`">
            <div>
              <strong>{{ file.name }}</strong>
              <small>{{ Math.round(file.size / 1024) }} KB</small>
            </div>
            <button class="ghost-button" @click="scanStore.removeFile(index)">删除</button>
          </li>
          <li v-if="!selectedFiles.length" class="empty-state">还没有待处理文件。</li>
        </ul>
      </section>

      <section class="panel">
        <p class="eyebrow">Actions</p>
        <h2>开始处理</h2>
        <div class="button-row">
          <button class="primary-button" :disabled="scanStore.isSubmitting" @click="submitFiles">
            {{ scanStore.isSubmitting ? "处理中..." : "生成 PDF" }}
          </button>
          <button class="ghost-button" @click="scanStore.clearFiles()">清空文件</button>
          <button class="ghost-button" @click="scanStore.resetResult()">重置结果</button>
        </div>
        <p v-if="scanStore.errorMessage" class="inline-error">{{ scanStore.errorMessage }}</p>
      </section>

      <section class="panel">
        <p class="eyebrow">Result</p>
        <h2>结果下载</h2>
        <p v-if="scanStore.pdfBlobUrl">扫描已完成，可以直接下载生成的 PDF。</p>
        <p v-else>提交后，后端会同步返回一份多页 PDF 文件。</p>
        <a v-if="scanStore.pdfBlobUrl" class="primary-button button-like" :href="scanStore.pdfBlobUrl" download="scan-result.pdf">
          下载 PDF
        </a>
      </section>
    </div>
  </AppShell>
</template>
