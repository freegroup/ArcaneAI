import { createStore } from 'vuex';
import game from './game';
import games from './games';
import sounds from "./sounds";
import encounters from "./encounters";

const store = createStore({
  modules: {
    game,
    games,
    sounds,
    encounters,
  },
});

export default store;
