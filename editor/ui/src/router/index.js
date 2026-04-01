// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router';
import CanvasGame from '../views/CanvasGame.vue';
import CanvasEncounter from '../views/CanvasEncounter.vue';
import Personality from '../views/Personality.vue';
import WelcomePrompt from '../views/WelcomePrompt.vue';
import Inventory from '../views/Inventory.vue';

const routes = [
  {
    path: '/',
    name: 'home',
    component: { render: () => null }
  },
  {
    path: '/game/:gameName([^/]+)',
    redirect: to => `/game/${to.params.gameName}/world`
  },
  {
    path: '/game/:gameName([^/]+)/personality',
    name: 'personality',
    component: Personality,
    props: true
  },
  {
    path: '/game/:gameName([^/]+)/welcome',
    name: 'welcome-prompt',
    component: WelcomePrompt,
    props: true
  },
  {
    path: '/game/:gameName([^/]+)/world',
    name: 'world',
    component: CanvasGame,
    props: true
  },
  {
    path: '/game/:gameName([^/]+)/encounter/:encounterName',
    name: 'encounter',
    component: CanvasEncounter,
    props: true
  },
  {
    path: '/game/:gameName([^/]+)/inventory',
    name: 'inventory',
    component: Inventory,
    props: true
  },
  {
    // Catch /game, /game/, and anything else unmatched
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
});

export default router;
