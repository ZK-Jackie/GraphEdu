import '@/assets/styles/main.css'
import 'virtual:svg-icons-register'
import 'ant-design-vue/dist/reset.css'

import App from '@/App.vue'
import router from '@/router'
import plugins from '@/plugins'
import stores from '@/stores'
import directives from '@/directives'
import useAppStore from '@/stores/modules/app'

const app = createApp(App)

app.use(stores)
app.use(router)
app.use(plugins)
app.use(directives)

// 初始化暗色模式
const appStore = useAppStore()
appStore.initDarkMode()
appStore.initLocale()
appStore.initTimeConfig()

app.mount('#app')
