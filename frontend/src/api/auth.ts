import { apiClient } from "./client";
import type { ApiMessage, LoginResponse, User } from "../types";

export async function registerAccount(username: string, password: string) {
  const response = await apiClient.post<{ message: string; user: User }>("/api/auth/register", {
    username,
    password
  });
  return response.data;
}

export async function loginAccount(username: string, password: string) {
  const response = await apiClient.post<LoginResponse>("/api/auth/login", {
    username,
    password
  });
  return response.data;
}

export async function fetchCurrentUser() {
  const response = await apiClient.get<{ user: User }>("/api/auth/me");
  return response.data.user;
}

export async function updatePassword(oldPassword: string, newPassword: string) {
  const response = await apiClient.patch<ApiMessage>("/api/auth/password", {
    old_password: oldPassword,
    new_password: newPassword
  });
  return response.data;
}
