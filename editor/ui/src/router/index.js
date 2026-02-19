// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router';
import CanvasGame from '../views/CanvasGame.vue';
import CanvasEncounter from '../views/CanvasEncounter.vue';
import GameSetup from '../views/PromptEdit_normal.vue';
import Inventory from '../views/Inventory.vue';

const routes = [
  {
    path: '/',
    redirect: '/game'
  },
  {
    path: '/game',
    name: 'game-selection',
    component: GameSetup,
    props: true
  },
  {
    path: '/game/:gameName',
    redirect: to => {
      // Redirect to world view
      return `/game/${to.params.gameName}/world`;
    }
  },
  {
    path: '/game/:gameName/personality',
    name: 'personality',
    component: GameSetup,
    props: true
  },
  {
    path: '/game/:gameName/world',
    name: 'world',
    component: CanvasGame,
    props: true
  },
  {
    path: '/game/:gameName/encounter/:encounterName',
    name: 'encounter',
    component: CanvasEncounter,
    props: true
  },
  {
    path: '/game/:gameName/inventory',
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
