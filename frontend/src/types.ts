export type UserRole = "user" | "admin";
export type UserStatus = "active" | "disabled";

export interface User {
  id: number;
  username: string;
  role: UserRole;
  status: UserStatus;
  created_at: string | null;
  updated_at: string | null;
}

export interface LoginResponse {
  token: string;
  user: User;
}

export interface ApiMessage {
  message: string;
}
