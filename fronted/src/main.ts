// ============================================================
// FlowMind AI Workspace — Entry Point
// ============================================================
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'highlight.js/styles/github-dark.css'
import App from './App.vue'
import './styles/index.css'

const app = createApp(App)
app.use(createPinia())
app.use(ElementPlus)
app.mount('#app')