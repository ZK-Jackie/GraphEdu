import type { DictState } from '@/types/stores/dict.ts'

const useDictStore = defineStore('dict', {
  state: (): DictState => {
    return {
      dict: [],
    }
  },

  actions: {
    /**
     * 获取字典
     * @param key 字典类型键
     * @returns 字典数据列表
     */
    getDict(key: string) {
      if (key == null || key === '') {
        return null
      }
      try {
        for (let i = 0; i < this.dict.length; i++) {
          if (this.dict[i]!.key === key) {
            return this.dict[i]!.value
          }
        }
      } catch (_e) {
        return null
      }
      return null
    },

    /**
     * 设置字典
     * @param key 字典类型键
     * @param value 字典数据列表
     */
    setDict(key: string, value: any[]) {
      if (key !== null && key !== '') {
        this.dict.push({
          key,
          value,
        })
      }
    },

    /**
     * 删除字典
     * @param key 字典类型键
     * @returns 是否删除成功
     */
    removeDict(key: string) {
      try {
        for (let i = 0; i < this.dict.length; i++) {
          if (this.dict[i]!.key === key) {
            this.dict.splice(i, 1)
            return true
          }
        }
      } catch (_e) {
        return false
      }
      return false
    },

    /**
     * 清空所有字典缓存
     */
    cleanDict() {
      this.dict = []
    },
  },
})

export default useDictStore
