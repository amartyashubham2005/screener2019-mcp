import { api } from "./api";

interface SignInData {
  email: string;
  password: string;
}

interface SignUpData {
  email: string;
  password: string;
}

interface AuthResponse {
  user: {
    id: string;
    email: string;
    full_name: string;
  };
  message: string;
}

export const authService = {
  async signIn(credentials: SignInData) {
    return api.post<AuthResponse>("/api/v1/signin", credentials);
  },

  async signUp(userData: SignUpData) {
    return api.post<AuthResponse>("/api/v1/signup", userData);
  },

  async signOut() {
    return api.post<AuthResponse>("/api/v1/signout");
  },
};