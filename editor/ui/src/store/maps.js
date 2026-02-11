import axios from 'axios';

const API_BASE_URL = process.env.VUE_APP_API_BASE_URL;

export default {
  namespaced: true,
  state: {
    maps: [],
    mapConfig: {
      system_prompt: "game prompt",
      final_prompt:"final prompt",
      inventory: [],
    },
    mapDiagram: [],
    mapName: "unknown",
    loading: false,
    error: null,
    _updateSource: null, // Track update source: 'canvas' | 'vue' | null
  },
  mutations: {
    SET_MAPS(state, maps) {
      state.maps = maps;
    },
    SET_MAP_CONFIG(state, data) {
      state.mapConfig = data;
    },
    ADD_INVENTORY_ITEM(state, item) {
      state.mapConfig.inventory.push(item);
    },
    UPDATE_INVENTORY_ITEM(state, { index, item }) {
      state.mapConfig.inventory.splice(index, 1, item);
    },
    REMOVE_INVENTORY_ITEM(state, index) {
      state.mapConfig.inventory.splice(index, 1);
    },
    SET_MAP_DIAGRAM(state, data) {
      state.mapDiagram = data;
    },
    SET_LOADING(state, isLoading) {
      state.loading = isLoading;
    },
    SET_ERROR(state, error) {
      state.error = error;
    },
    SET_MAP_NAME(state, newName) {
      state.mapName = newName;
    },
    SET_UPDATE_SOURCE(state, source) {
      state._updateSource = source;
    },
  },
  actions: {
    async initialize({ dispatch }) {
      try {
        console.log(dispatch)
        //await dispatch('downloadConversation', 'zork.json');
        //await dispatch('downloadConversation', 'fsm_fun.json');
        //await dispatch('downloadConversation', 'fsm_techi.json');
      } catch (error) {
        console.error('Failed to load default map:', error);
      }
    },

    async fetchMaps({ commit }) {
      commit('SET_LOADING', true);
      commit('SET_ERROR', null);
      try {
        const response = await axios.get(`${API_BASE_URL}/maps/`);
        commit('SET_MAPS', response.data);
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.detail || 'Error fetching maps');
      } finally {
        commit('SET_LOADING', false);
      }
    },

    async downloadMap({ commit, dispatch }, mapName) {
      if( mapName===undefined || mapName.length===0){
        return // silently
      }

      commit('SET_LOADING', true);
      commit('SET_ERROR', null);
      try {
        const response = await axios.get(`${API_BASE_URL}/maps/${mapName}`, {
          responseType: 'blob',
        });
        const mapData = JSON.parse(await response.data.text()); 
        commit('SET_MAP_CONFIG', mapData.config); 
        commit('SET_MAP_DIAGRAM', mapData.diagram); 
        commit('SET_MAP_NAME', mapName);
        await dispatch('sounds/fetchSounds', mapName, { root: true });
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.detail || 'Error downloading file');
        throw error;
      } finally {
        commit('SET_LOADING', false);
      }
    },

    async createNewMap({ commit, dispatch }, mapName) {
      if( mapName===undefined || mapName.length===0){
        return // silently
      }

      commit('SET_LOADING', true);
      commit('SET_ERROR', null);
      try {
        const response = await axios.post(`${API_BASE_URL}/maps/${mapName}`, {
          responseType: 'blob',
        });
        const mapData = await response.data; 
        commit('SET_MAP_CONFIG', mapData.config); 
        commit('SET_MAP_DIAGRAM', mapData.diagram); 
        commit('SET_MAP_NAME', mapName);
        await dispatch('sounds/fetchSounds', mapName, { root: true });
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.detail || 'Error downloading file');
        throw error;
      } finally {
        commit('SET_LOADING', false);
      }
    },

    async updateMapConfig({ commit }, data) {
      commit('SET_MAP_CONFIG', data);
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
    async updateMapDiagram({ commit }, data) {
      // Mark that this update came from canvas
      commit('SET_UPDATE_SOURCE', 'canvas');
      commit('SET_MAP_DIAGRAM', data);
      
      // Auto-reset source after a short delay to allow watch to process
      setTimeout(() => {
        commit('SET_UPDATE_SOURCE', null);
      }, 100);
    },

    async saveMap({ commit, state }) {
      commit('SET_LOADING', true);
      commit('SET_ERROR', null);
      try {
        // Simple: Just save the JSON with config and diagram
        const formattedJson = JSON.stringify({
          "config": state.mapConfig,
          "diagram": state.mapDiagram
        }, null, 4);

        const blob = new Blob([formattedJson], { type: 'application/json' });
        const formData = new FormData();
        formData.append('file', blob, state.mapName + ".json");

        // Send PUT request to backend - that's it!
        await axios.put(`${API_BASE_URL}/maps/`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.detail || 'Error saving document');
        throw error;
      } finally {
        commit('SET_LOADING', false);
      }
    },
  },
  getters: {
    maps: (state) => state.maps,
    mapConfig: (state) => state.mapConfig,
    mapDiagram: (state) => state.mapDiagram,
    mapName: (state) => state.mapName,
    isLoading: (state) => state.loading,
    error: (state) => state.error,
    updateSource: (state) => state._updateSource,
  },
};
