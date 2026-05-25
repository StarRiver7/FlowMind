// ============================================================
// FlowMind — Entry Point (vben architecture)
// ============================================================
import { createApp } from 'vue'
import { pinia } from './store'
import router from './router'
import App from './App.vue'

// Global styles
import './styles/index.css'

const app = createApp(App)

app.use(pinia)
app.use(router)

app.mount('#app')