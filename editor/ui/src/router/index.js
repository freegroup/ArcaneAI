// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router';
import StateCanvas from '../views/StateCanvas.vue';
import Configuration from '../views/Configuration.vue';
import Inventory from '../views/Inventory.vue';

const routes = [
  {
    path: '/diagram/:fileName?',
    name: 'diagram',
    component: StateCanvas,
    props: true
  },
  {
    path: '/configuration/:fileName?',
    name: 'configuration',
    component: Configuration,
    props: true
  },
  {
    path: '/inventory/:fileName?',
    name: 'inventory',
    component: Inventory,
    props: true
  }
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
});

export default router;
