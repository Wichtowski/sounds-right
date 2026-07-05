"use client";

export { ApiClient } from "./client";
export { authResponseSchema, clearToken, getToken, setToken } from "./auth";
export type * from "./types";

import { ApiClient } from "./client";

export const api = new ApiClient();
