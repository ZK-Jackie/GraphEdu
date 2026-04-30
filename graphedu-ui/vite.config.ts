import { fileURLToPath, URL } from 'node:url'
import { defineConfig, loadEnv, UserConfig } from 'vite'
import createVitePlugins from './vite/plugins'
// import { type RolldownOptions } from 'rolldown'
// https://vite.dev/config/
export default defineConfig(({ command, mode }) => {
  // https://cn.vite.dev/config/#using-environment-variables-in-config
  const env = loadEnv(mode, process.cwd()) as any
  // config
  return {
    base: env.VITE_BASE_URL || '/',
    plugins: createVitePlugins(env, command),
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    build: {
      sourcemap: false,
      minify: 'esbuild',
      // vite 8.0 +，rolldown 与 antdv 4.x 有兼容性问题，待转用 antdv-next 后再更新
      // rolldownOptions: {
      //   output: {
      //     minify: {
      //       compress: {
      //         dropConsole: true,
      //         dropDebugger: true
      //       },
      //     },
      //   },
      // } as RolldownOptions,
    },
    // vite 7
    esbuild: {
      drop: ['console', 'debugger'],
    },
    // https://cn.vite.dev/config/server-options#server-proxy
    server: {
      host: '0.0.0.0',
      port: 8001,
      open: false,
      proxy: {
        '/dev-api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/dev-api/, ''),
        },
      },
    },
  } as UserConfig
})
