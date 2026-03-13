const STORAGE_KEY = 'arcaneai-theme';
const DEFAULT_THEME = 'dark';

const THEMES = [
  { id: 'dark', label: 'Dark Fantasy' },
  { id: 'tavern', label: 'Fantasy Tavern' },
  { id: 'elegant', label: 'Elegant' },
];

export default {
  namespaced: true,

  state: () => ({
    theme: localStorage.getItem(STORAGE_KEY) || DEFAULT_THEME,
  }),

  getters: {
    currentTheme: (state) => state.theme,
    availableThemes: () => THEMES,
  },

  mutations: {
    SET_THEME(state, theme) {
      state.theme = theme;
      localStorage.setItem(STORAGE_KEY, theme);
      // 'dark' is the default (:root), so remove attribute; others set data-theme
      if (theme === DEFAULT_THEME) {
        document.documentElement.removeAttribute('data-theme');
      } else {
        document.documentElement.setAttribute('data-theme', theme);
      }
    },
  },

  actions: {
    initTheme({ state, commit }) {
      // Apply persisted theme on app startup
      commit('SET_THEME', state.theme);
    },
    setTheme({ commit }, theme) {
      commit('SET_THEME', theme);
    },
  },
};
