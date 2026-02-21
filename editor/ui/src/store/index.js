import { createStore } from 'vuex';
// Legacy stores (für Rückwärtskompatibilität)
import game from './game';
import games from './games';
import sounds from "./sounds";
import encounters from "./encounters";

// New Overlay Pattern stores
import model from './model';
import views from './views';
import config from './config';

const store = createStore({
  modules: {
    // Legacy modules
    game,
    games,
    sounds,
    encounters,
    
    // New Overlay Pattern modules
    model,
    views,
    config,
  },
});

export default store;
