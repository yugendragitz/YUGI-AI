export type UserRole = "USER" | "ADMIN" | "MODERATOR";

export interface User {
  id: string;
  email: string;
  username: string;
  display_name: string;
  role: UserRole;
  is_active: boolean;
  is_verified: boolean;
  avatar_seed: string;
  avatar_style: string;
  avatar_url: string | null;
  last_login_at: string | null;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface MessageResponse {
  message: string;
  detail?: string | null;
}
