<script setup lang="ts">
const emit = defineEmits<{
  (event: "files-selected", files: File[]): void;
}>();

function onFileChange(event: Event) {
  const target = event.target as HTMLInputElement;
  const files = Array.from(target.files || []);
  emit("files-selected", files);
  target.value = "";
}

function onDrop(event: DragEvent) {
  event.preventDefault();
  const files = Array.from(event.dataTransfer?.files || []);
  emit("files-selected", files);
}
</script>

<template>
  <label class="dropzone" @dragover.prevent @drop="onDrop">
    <input type="file" accept="image/*" multiple hidden @change="onFileChange" />
    <p class="dropzone__title">拖拽图片到这里，或点击选择文件</p>
    <p class="dropzone__hint">支持 PNG / JPG / JPEG / BMP / WEBP，可分批追加。</p>
  </label>
</template>
