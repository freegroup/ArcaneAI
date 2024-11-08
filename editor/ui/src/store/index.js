import { createStore } from 'vuex';
import maps from './maps';
import sounds from "./sounds";

export default createStore({
  modules: {
    maps,
    sounds,
  },
});
