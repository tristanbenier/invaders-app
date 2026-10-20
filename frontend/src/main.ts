import 'leaflet/dist/leaflet.css'
import 'leaflet.markercluster/dist/MarkerCluster.css'
import './styles/main.css'

import { createPinia } from 'pinia'
import { createApp } from 'vue'

import App from './App.vue'
import { router } from './router'

createApp(App).use(createPinia()).use(router).mount('#app')
