import { createStore } from 'vuex';
import game from './game';
import games from './games';
import sounds from "./sounds";
import encounters from "./encounters";
import { createDiagramManager } from '@/utils/DiagramManager';

const store = createStore({
  modules: {
    game,
    games,
    sounds,
    encounters,
  },
});

// Initialize DiagramManager singleton
export const diagramManager = createDiagramManager(store);

export default store;