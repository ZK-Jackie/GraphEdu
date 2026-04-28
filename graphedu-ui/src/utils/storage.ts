import Cookies from 'js-cookie'

const cookieSet = {
  set(key: string, value: string, expireDays: number | null = null): void {
    if (key != null && value != null) {
      if (expireDays != null) {
        Cookies.set(key, value, { expires: expireDays })
      } else {
        Cookies.set(key, value)
      }
    }
  },
  get(key: string): string | undefined {
    if (key == null) {
      return undefined
    }
    return Cookies.get(key)
  },
  remove(key: string): void {
    Cookies.remove(key)
  },
}

const sessionCache = {
  set(key: string, value: string): void {
    if (!sessionStorage) {
      return
    }
    if (key != null && value != null) {
      sessionStorage.setItem(key, value)
    }
  },
  get(key: string): string | null {
    if (!sessionStorage) {
      return null
    }
    if (key == null) {
      return null
    }
    return sessionStorage.getItem(key)
  },
  setJSON(key: string, jsonValue: any): void {
    if (jsonValue != null) {
      this.set(key, JSON.stringify(jsonValue))
    }
  },
  getJSON(key: string): any {
    const value = this.get(key)
    if (value != null) {
      return JSON.parse(value)
    }
    return null
  },
  remove(key: string): void {
    sessionStorage.removeItem(key)
  },
}
const localCache = {
  set(key: string, value: string) {
    if (!localStorage) {
      return
    }
    if (key != null && value != null) {
      localStorage.setItem(key, value)
    }
  },
  get(key: string): string | null {
    if (!localStorage) {
      return null
    }
    if (key == null) {
      return null
    }
    return localStorage.getItem(key)
  },
  setJSON(key: string, jsonValue: any): void {
    if (jsonValue != null) {
      this.set(key, JSON.stringify(jsonValue))
    }
  },
  getJSON(key: string): any {
    const value = this.get(key)
    if (value != null) {
      return JSON.parse(value)
    }
    return null
  },
  remove(key: string): void {
    localStorage.removeItem(key)
  },
}

export default {
  /**
   * 基于 Cookie 的缓存
   */
  cookies: cookieSet,
  /**
   * 会话级缓存
   */
  session: sessionCache,
  /**
   * 本地缓存
   */
  local: localCache,
}
