import { createStore } from 'vuex';
import conversations from './conversations';
import sounds from "./sounds";

export default createStore({
  modules: {
    conversations,
    sounds,
  },
});
