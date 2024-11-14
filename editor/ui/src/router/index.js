// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router';
import StateCanvas from '../views/StateCanvas.vue';
import GameSetup from '../views/GameSetup.vue';
import EndgameSetup from '../views/EndgameSetup.vue';
import Inventory from '../views/Inventory.vue';

const routes = [
  {
    path: '/',
    redirect: '/gamesetup'
  },
  {
    path: '/gamesetup/:mapName?',
    name: 'gamesetup',
    component: GameSetup,
    props: true
  },
  {
    path: '/endgamesetup/:mapName?',
    name: 'endgamesetup',
    component: EndgameSetup,
    props: true
  },
  {
    path: '/diagram/:mapName?',
    name: 'diagram',
    component: StateCanvas,
    props: true
  },
  {
    path: '/inventory/:mapName?',
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
