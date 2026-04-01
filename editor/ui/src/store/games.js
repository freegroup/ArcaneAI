import axios from 'axios';

const API_BASE_URL = process.env.VUE_APP_API_BASE_URL;
const RECENT_GAMES_KEY = 'arcaneai-recent-games';
const MAX_RECENT_GAMES = 5;

export default {
  namespaced: true,
  state: {
    games: [],
    recentGames: [],
    currentGameName: null,
    loading: false,
    error: null,
  },
  mutations: {
    SET_GAMES(state, games) {
      state.games = games;
    },
    SET_RECENT_GAMES(state, recentGames) {
      state.recentGames = recentGames;
    },
    SET_CURRENT_GAME_NAME(state, gameName) {
      state.currentGameName = gameName;
    },
    SET_LOADING(state, isLoading) {
      state.loading = isLoading;
    },
    SET_ERROR(state, error) {
      state.error = error;
    },
  },
  actions: {
    async initialize({ dispatch }) {
      await dispatch('fetchGames');
      await dispatch('loadRecentGames');
    },

    async fetchGames({ commit }) {
      commit('SET_LOADING', true);
      commit('SET_ERROR', null);
      try {
        const response = await axios.get(`${API_BASE_URL}/games/`);
        commit('SET_GAMES', response.data);
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.detail || 'Error fetching games');
      } finally {
        commit('SET_LOADING', false);
      }
    },

    loadRecentGames({ commit, state }) {
      try {
        const stored = localStorage.getItem(RECENT_GAMES_KEY);
        const all = stored ? JSON.parse(stored) : [];
        const filtered = all
          .filter(entry => state.games.includes(entry.name))
          .sort((a, b) => b.lastOpened - a.lastOpened)
          .slice(0, MAX_RECENT_GAMES);
        commit('SET_RECENT_GAMES', filtered);
      } catch {
        commit('SET_RECENT_GAMES', []);
      }
    },

    addRecentGame({ commit, state }, gameName) {
      try {
        const updated = [
          { name: gameName, lastOpened: Date.now() },
          ...state.recentGames.filter(e => e.name !== gameName),
        ].slice(0, MAX_RECENT_GAMES);
        commit('SET_RECENT_GAMES', updated);
        localStorage.setItem(RECENT_GAMES_KEY, JSON.stringify(updated));
      } catch {
        // localStorage unavailable — silent fallback
      }
    },

    removeRecentGame({ commit, state }, gameName) {
      try {
        const updated = state.recentGames.filter(e => e.name !== gameName);
        commit('SET_RECENT_GAMES', updated);
        localStorage.setItem(RECENT_GAMES_KEY, JSON.stringify(updated));
      } catch {
        // localStorage unavailable — silent fallback
      }
    },

    async createNewGame({ commit, dispatch }, gameName) {
      if( gameName===undefined || gameName.length===0){
        return // silently
      }

      commit('SET_LOADING', true);
      commit('SET_ERROR', null);
      try {
        // POST to /games with name in body (RESTful - create resource)
        const response = await axios.post(`${API_BASE_URL}/games/`, { name: gameName });

        // Use the sanitized name returned by the backend
        const actualGameName = response.data.game_name || gameName;

        // Load the newly created game into the game store
        await dispatch('game/loadGame', actualGameName, { root: true });
        commit('SET_CURRENT_GAME_NAME', actualGameName);

        // Refresh the games list
        await dispatch('fetchGames');
        dispatch('addRecentGame', actualGameName);

        // Return the actual game name so the caller can use it for navigation
        return actualGameName;
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.detail || 'Error creating game');
        throw error;
      } finally {
        commit('SET_LOADING', false);
      }
    },

    async selectGame({ commit, dispatch }, gameName) {
      if( gameName===undefined || gameName.length===0){
        return // silently
      }

      commit('SET_LOADING', true);
      commit('SET_ERROR', null);
      try {
        // Load the game into the game store
        await dispatch('game/loadGame', gameName, { root: true });
        commit('SET_CURRENT_GAME_NAME', gameName);
        dispatch('addRecentGame', gameName);
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.detail || 'Error selecting game');
        throw error;
      } finally {
        commit('SET_LOADING', false);
      }
    },

    async deleteGame({ commit, dispatch }, gameName) {
      if( gameName===undefined || gameName.length===0){
        return // silently
      }

      commit('SET_LOADING', true);
      commit('SET_ERROR', null);
      try {
        await axios.delete(`${API_BASE_URL}/games/${gameName}`);

        // Refresh the games list
        await dispatch('fetchGames');
        dispatch('removeRecentGame', gameName);

        // If this was the current game, clear it
        if (gameName === commit.state.currentGameName) {
          commit('SET_CURRENT_GAME_NAME', null);
        }
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.detail || 'Error deleting game');
        throw error;
      } finally {
        commit('SET_LOADING', false);
      }
    },
  },
  getters: {
    games: (state) => state.games,
    recentGames: (state) => state.recentGames,
    currentGameName: (state) => state.currentGameName,
    isLoading: (state) => state.loading,
    error: (state) => state.error,
  },
};
