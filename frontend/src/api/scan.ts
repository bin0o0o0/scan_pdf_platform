import { apiClient } from "./client";

export async function submitScan(files: File[]) {
  const formData = new FormData();

  // 后端约定字段名为 files[]，前端需要显式保持一致，
  // 否则 Flask 端的 request.files.getlist("files[]") 就拿不到完整列表。
  files.forEach((file) => {
    formData.append("files[]", file);
  });

  const response = await apiClient.post<Blob>("/api/scan", formData, {
    responseType: "blob"
  });

  return response.data;
}
