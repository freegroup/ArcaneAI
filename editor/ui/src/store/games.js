import axios from 'axios';

const API_BASE_URL = process.env.VUE_APP_API_BASE_URL;

export default {
  namespaced: true,
  state: {
    games: [],
    currentGameName: null,
    loading: false,
    error: null,
  },
  mutations: {
    SET_GAMES(state, games) {
      state.games = games;
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
      try {
        // Placeholder for future initialization
        void dispatch; // Suppress unused variable warning
      } catch (error) {
        // Silent error handling
      }
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

    async createNewGame({ commit, dispatch }, gameName) {
      if( gameName===undefined || gameName.length===0){
        return // silently
      }

      commit('SET_LOADING', true);
      commit('SET_ERROR', null);
      try {
        await axios.post(`${API_BASE_URL}/games/${gameName}`, {
          responseType: 'blob',
        });
        
        // Load the newly created game into the game store
        await dispatch('game/loadGame', gameName, { root: true });
        commit('SET_CURRENT_GAME_NAME', gameName);
        
        // Refresh the games list
        await dispatch('fetchGames');
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
    currentGameName: (state) => state.currentGameName,
    isLoading: (state) => state.loading,
    error: (state) => state.error,
  },
};