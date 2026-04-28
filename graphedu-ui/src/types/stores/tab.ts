import type { Tab } from '@/types/components/tab.ts'

export interface TabState {
  visitedTabs: Array<Tab>
  cachedTabs: Array<string>
  cachedLayout: Array<string>
}
