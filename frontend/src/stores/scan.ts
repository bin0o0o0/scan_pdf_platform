import { ref } from "vue";
import { defineStore } from "pinia";

import { submitScan } from "../api/scan";

export const useScanStore = defineStore("scan", () => {
  const selectedFiles = ref<File[]>([]);
  const isSubmitting = ref(false);
  const errorMessage = ref("");
  const pdfBlobUrl = ref("");

  function addFiles(files: File[]) {
    // 这里做追加而不是覆盖，是为了支持“分批选择图片再一起提交”。
    selectedFiles.value = [...selectedFiles.value, ...files];
  }

  function removeFile(index: number) {
    selectedFiles.value = selectedFiles.value.filter((_, currentIndex) => currentIndex !== index);
  }

  function clearFiles() {
    selectedFiles.value = [];
    resetResult();
  }

  function resetResult() {
    errorMessage.value = "";
    if (pdfBlobUrl.value) {
      // createObjectURL 创建出来的是浏览器侧临时地址，用完要主动释放。
      URL.revokeObjectURL(pdfBlobUrl.value);
    }
    pdfBlobUrl.value = "";
  }

  async function submitFiles() {
    resetResult();
    isSubmitting.value = true;

    try {
      const pdfBlob = await submitScan(selectedFiles.value);
      pdfBlobUrl.value = URL.createObjectURL(pdfBlob);
      return pdfBlobUrl.value;
    } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : "扫描失败。";
      throw error;
    } finally {
      isSubmitting.value = false;
    }
  }

  return {
    selectedFiles,
    isSubmitting,
    errorMessage,
    pdfBlobUrl,
    addFiles,
    removeFile,
    clearFiles,
    submitFiles,
    resetResult
  };
});
