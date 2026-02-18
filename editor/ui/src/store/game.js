import axios from 'axios';

const API_BASE_URL = process.env.VUE_APP_API_BASE_URL;

export default {
  namespaced: true,
  state: {
    gameConfig: {
      system_prompt: "game prompt",
      final_prompt:"final prompt",
      inventory: [],
    },
    gameDiagram: [],
    gameName: "unknown",
    loading: false,
    error: null,
    _updateSource: null, // Track update source: 'canvas' | 'vue' | null
  },
  mutations: {
    SET_GAME_CONFIG(state, data) {
      state.gameConfig = data;
    },
    ADD_INVENTORY_ITEM(state, item) {
      state.gameConfig.inventory.push(item);
    },
    UPDATE_INVENTORY_ITEM(state, { index, item }) {
      state.gameConfig.inventory.splice(index, 1, item);
    },
    REMOVE_INVENTORY_ITEM(state, index) {
      state.gameConfig.inventory.splice(index, 1);
    },
    SET_GAME_DIAGRAM(state, data) {
      state.gameDiagram = data;
    },
    SET_LOADING(state, isLoading) {
      state.loading = isLoading;
    },
    SET_ERROR(state, error) {
      state.error = error;
    },
    SET_GAME_NAME(state, newName) {
      state.gameName = newName;
    },
    SET_UPDATE_SOURCE(state, source) {
      state._updateSource = source;
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

    async loadGame({ commit, dispatch }, gameName) {
      if( gameName===undefined || gameName.length===0){
        return // silently
      }

      commit('SET_LOADING', true);
      commit('SET_ERROR', null);
      try {
        const response = await axios.get(`${API_BASE_URL}/game/${gameName}`, {
          responseType: 'blob',
        });
        const gameData = JSON.parse(await response.data.text()); 
        commit('SET_GAME_CONFIG', gameData.config); 
        commit('SET_GAME_DIAGRAM', gameData.diagram); 
        commit('SET_GAME_NAME', gameName);
        
        // Load related resources for this game
        await dispatch('sounds/fetchSounds', gameName, { root: true });
        await dispatch('encounters/fetchEncounters', gameName, { root: true });
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.detail || 'Error loading game');
        throw error;
      } finally {
        commit('SET_LOADING', false);
      }
    },

    async updateGameConfig({ commit }, data) {
      commit('SET_GAME_CONFIG', data);
    },
    
    addInventoryItem({ commit }, item) {
      commit('ADD_INVENTORY_ITEM', item);
    },
    
    updateInventoryItem({ commit }, { index, item }) {
      commit('UPDATE_INVENTORY_ITEM', { index, item });
    },
    
    removeInventoryItem({ commit }, index) {
      commit('REMOVE_INVENTORY_ITEM', index);
    },
    
    async updateGameDiagram({ commit }, data) {
      // Mark that this update came from canvas
      commit('SET_UPDATE_SOURCE', 'canvas');
      commit('SET_GAME_DIAGRAM', data);
      
      // Auto-reset source after a short delay to allow watch to process
      setTimeout(() => {
        commit('SET_UPDATE_SOURCE', null);
      }, 100);
    },

    async saveGame({ commit, state }) {
      commit('SET_LOADING', true);
      commit('SET_ERROR', null);
      try {
        // Simple: Just save the JSON with config and diagram
        const formattedJson = JSON.stringify({
          "config": state.gameConfig,
          "diagram": state.gameDiagram
        }, null, 4);

        const blob = new Blob([formattedJson], { type: 'application/json' });
        const formData = new FormData();
        formData.append('file', blob, state.gameName + ".json");

        // Send PUT request to backend - that's it!
        await axios.put(`${API_BASE_URL}/game/${state.gameName}`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.detail || 'Error saving game');
        throw error;
      } finally {
        commit('SET_LOADING', false);
      }
    },
  },
  getters: {
    gameConfig: (state) => state.gameConfig,
    gameDiagram: (state) => state.gameDiagram,
    gameName: (state) => state.gameName,
    isLoading: (state) => state.loading,
    error: (state) => state.error,
    updateSource: (state) => state._updateSource,
  },
};