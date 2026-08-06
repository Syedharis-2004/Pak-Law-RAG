/**
 * PakLaw AI — Authentication Utilities
 * Handles JWT token management, user session, and auth helpers
 */

export const TOKEN_KEY = "paklaw_token";
export const USER_KEY = "paklaw_user";

export interface UserPayload {
  id: string;
  email: string;
  full_name: string;
  roles: string[];
  is_active: boolean;
}

/**
 * Store auth token in localStorage
 */
export function setToken(token: string): void {
  if (typeof window !== "undefined") {
    localStorage.setItem(TOKEN_KEY, token);
  }
}

/**
 * Retrieve auth token from localStorage
 */
export function getToken(): string | null {
  if (typeof window !== "undefined") {
    return localStorage.getItem(TOKEN_KEY);
  }
  return null;
}

/**
 * Remove auth token (logout)
 */
export function clearToken(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }
}

/**
 * Store user profile in localStorage
 */
export function setUser(user: UserPayload): void {
  if (typeof window !== "undefined") {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  }
}

/**
 * Retrieve current user profile
 */
export function getUser(): UserPayload | null {
  if (typeof window !== "undefined") {
    const raw = localStorage.getItem(USER_KEY);
    if (raw) {
      try {
        return JSON.parse(raw) as UserPayload;
      } catch {
        return null;
      }
    }
  }
  return null;
}

/**
 * Check if user is currently authenticated (has valid token)
 */
export function isAuthenticated(): boolean {
  const token = getToken();
  if (!token) return false;

  try {
    // Decode JWT payload (without verification — server handles that)
    const payloadBase64 = token.split(".")[1];
    if (!payloadBase64) return false;
    const payload = JSON.parse(atob(payloadBase64));
    // Check expiry
    if (payload.exp && Date.now() / 1000 > payload.exp) {
      clearToken();
      return false;
    }
    return true;
  } catch {
    return false;
  }
}

/**
 * Check if current user has a given role
 */
export function hasRole(role: string): boolean {
  const user = getUser();
  return user?.roles?.includes(role) ?? false;
}

/**
 * Check if current user is an admin
 */
export function isAdmin(): boolean {
  return hasRole("admin") || hasRole("super_admin");
}

/**
 * Redirect to login if not authenticated
 * @param router - optional Next.js router
 */
export function requireAuth(redirectPath = "/auth/login"): void {
  if (typeof window !== "undefined" && !isAuthenticated()) {
    window.location.href = redirectPath;
  }
}

/**
 * Perform logout: clear storage and redirect
 */
export function logout(redirectPath = "/auth/login"): void {
  clearToken();
  if (typeof window !== "undefined") {
    window.location.href = redirectPath;
  }
}
