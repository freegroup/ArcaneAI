import { createStore } from 'vuex';
import game from './game';
import games from './games';
import sounds from "./sounds";
import encounters from "./encounters";

export default createStore({
  modules: {
    game,
    games,
    sounds,
    encounters,
  },
});
