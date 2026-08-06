const UID_STORAGE_KEY = 'user_uid';

/**
 * Get UID from localStorage (client-side only)
 */
export function getUID(): string | null {
  if (typeof window === 'undefined') {
    return null;
  }
  return localStorage.getItem(UID_STORAGE_KEY);
}

/**
 * Set UID in localStorage (client-side only)
 */
export function setUID(uid: string): void {
  if (typeof window === 'undefined') {
    return;
  }
  localStorage.setItem(UID_STORAGE_KEY, uid);
}

/**
 * Clear UID from localStorage (client-side only)
 */
export function clearUID(): void {
  if (typeof window === 'undefined') {
    return;
  }
  localStorage.removeItem(UID_STORAGE_KEY);
}

/**
 * Check if user is authenticated (has UID)
 */
export function isAuthenticated(): boolean {
  return getUID() !== null;
}
