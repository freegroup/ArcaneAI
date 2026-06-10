// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router';
import CanvasGame from '../views/CanvasGame.vue';
import CanvasEncounter from '../views/CanvasEncounter.vue';
import Personality from '../views/Personality.vue';
import WelcomePrompt from '../views/WelcomePrompt.vue';
import GameTarget from '../views/GameTarget.vue';
import HelpText from '../views/HelpText.vue';
import Inventory from '../views/Inventory.vue';
import RoomsEmptyState from '../views/RoomsEmptyState.vue';
import RoomDetail from '../views/RoomDetail.vue';

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
    path: '/game/:gameName([^/]+)/game-target',
    name: 'game-target',
    component: GameTarget,
    props: true
  },
  {
    path: '/game/:gameName([^/]+)/help-text',
    name: 'help-text',
    component: HelpText,
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
    path: '/game/:gameName([^/]+)/rooms',
    name: 'rooms-empty',
    component: RoomsEmptyState,
    props: true
  },
  {
    path: '/game/:gameName([^/]+)/rooms/:roomName',
    name: 'room-detail',
    component: RoomDetail,
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
