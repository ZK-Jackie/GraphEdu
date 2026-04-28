import storage from './storage.ts'
import { CookieAdminTokenKey } from '@/constants.ts'

export function getToken(): string | undefined {
  return storage.cookies.get(CookieAdminTokenKey)
}

export function setToken(token: string): void {
  storage.cookies.set(CookieAdminTokenKey, token)
}

export function removeToken(): void {
  storage.cookies.remove(CookieAdminTokenKey)
}
