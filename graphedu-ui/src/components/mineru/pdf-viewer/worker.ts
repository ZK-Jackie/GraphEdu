/**
 * pdfjs-dist Worker 初始化
 *
 * 使用 Vite 的 ?url 导入获取 worker 文件路径，
 * 避免 bundler 将整个 worker 打包进主 chunk。
 * 在使用 PDF 功能前需确保此模块已被导入（由 PdfViewer 组件自动导入）。
 */
import { GlobalWorkerOptions } from 'pdfjs-dist'

import workerUrl from 'pdfjs-dist/build/pdf.worker.min.mjs?url'

GlobalWorkerOptions.workerSrc = workerUrl
