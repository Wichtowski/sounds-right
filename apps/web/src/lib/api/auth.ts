import { z } from "zod";

const tokenKey = "sounds-right-access-token";

export const authResponseSchema = z.object({
  access_token: z.string().min(1),
});

export type AuthResponse = z.infer<typeof authResponseSchema>;

export function getToken() {
  if (typeof window === "undefined") {
    return null;
  }

  return window.localStorage.getItem(tokenKey);
}

export function setToken(token: string) {
  window.localStorage.setItem(tokenKey, token);
}

export function clearToken() {
  window.localStorage.removeItem(tokenKey);
}
