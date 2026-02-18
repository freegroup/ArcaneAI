import { createStore } from 'vuex';
import games from './games';
import sounds from "./sounds";

export default createStore({
  modules: {
    games,
    sounds,
  },
});
