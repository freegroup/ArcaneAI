import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'
import vuetify from './plugins/vuetify'
import { InstallCodeMirror } from "codemirror-editor-vue3";

import SoundManager from '@/utils/SoundManager'

// Import Game Theme CSS Variables
import './assets/game-theme.css'

SoundManager.initialize(store);

const app = createApp(App)

app.use(router)
app.use(store)
app.use(vuetify)
app.use(InstallCodeMirror);

app.mount('#app')
