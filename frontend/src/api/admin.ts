import { apiClient } from "./client";
import type { User, UserRole, UserStatus } from "../types";

export async function fetchUsers() {
  const response = await apiClient.get<{ users: User[] }>("/api/admin/users");
  return response.data.users;
}

export async function changeUserStatus(userId: number, status: UserStatus) {
  const response = await apiClient.patch<{ user: User }>(`/api/admin/users/${userId}/status`, {
    status
  });
  return response.data.user;
}

export async function changeUserRole(userId: number, role: UserRole) {
  const response = await apiClient.patch<{ user: User }>(`/api/admin/users/${userId}/role`, {
    role
  });
  return response.data.user;
}
