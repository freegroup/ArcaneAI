import axios from 'axios';

const API_BASE_URL = process.env.VUE_APP_API_BASE_URL;

export default {
  namespaced: true,
  state: {
    encounters: [],
    currentEncounter: null,
    loading: false,
    error: null,
  },
  mutations: {
    SET_ENCOUNTERS(state, encounters) {
      state.encounters = encounters;
    },
    SET_CURRENT_ENCOUNTER(state, encounter) {
      state.currentEncounter = encounter;
    },
    SET_LOADING(state, isLoading) {
      state.loading = isLoading;
    },
    SET_ERROR(state, error) {
      state.error = error;
    },
  },
  actions: {
    async initialize() {
      // Placeholder for future initialization
    },

    async fetchEncounters({ commit }, gameName) {
      if (!gameName || gameName.length === 0) {
        return; // silently
      }

      commit('SET_LOADING', true);
      commit('SET_ERROR', null);
      try {
        // First get the list of encounter names
        const namesResponse = await axios.get(`${API_BASE_URL}/game/${gameName}/encounters`);
        const encounterNames = namesResponse.data;
        
        // Then load ALL encounter data in parallel
        const encounterDataPromises = encounterNames.map(async (name) => {
          try {
            const response = await axios.get(
              `${API_BASE_URL}/game/${gameName}/encounters/${name}`,
              { responseType: 'text' }  // Get as text first
            );
            // Parse the JSON string to object
            const data = JSON.parse(response.data);
            return { name, data };
          } catch (error) {
            console.error(`[ENCOUNTERS] Error loading encounter ${name}:`, error);
            return { name, data: null, error: true };
          }
        });

        const encountersWithData = await Promise.all(encounterDataPromises);
        
        // Convert to object map: { '001_go': {...data...}, '002_tavern': {...data...} }
        const encountersMap = {};
        encountersWithData.forEach(({ name, data }) => {
          if (data) {
            encountersMap[name] = data;
          }
        });
        
        commit('SET_ENCOUNTERS', encountersMap);
        
        // Log to console
        console.log('[ENCOUNTERS] Loaded ALL encounters for game:', gameName);
        console.log('[ENCOUNTERS] Encounter data:', encountersMap);
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.detail || 'Error fetching encounters');
        console.error('[ENCOUNTERS] Error loading encounters:', error);
      } finally {
        commit('SET_LOADING', false);
      }
    },

    async loadEncounter({ commit }, { gameName, encounterName }) {
      if (!gameName || !encounterName) {
        return; // silently
      }

      commit('SET_LOADING', true);
      commit('SET_ERROR', null);
      try {
        const response = await axios.get(
          `${API_BASE_URL}/game/${gameName}/encounters/${encounterName}`,
          { responseType: 'blob' }
        );
        const encounterData = JSON.parse(await response.data.text());
        commit('SET_CURRENT_ENCOUNTER', encounterData);
        console.log('[ENCOUNTERS] Loaded encounter:', encounterName, encounterData);
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.detail || 'Error loading encounter');
        console.error('[ENCOUNTERS] Error loading encounter:', error);
      } finally {
        commit('SET_LOADING', false);
      }
    },

    async createEncounter({ commit, dispatch }, { gameName, encounterName, data }) {
      if (!gameName || !encounterName) {
        return; // silently
      }

      commit('SET_LOADING', true);
      commit('SET_ERROR', null);
      try {
        const formattedJson = JSON.stringify(data, null, 4);
        const blob = new Blob([formattedJson], { type: 'application/json' });
        const formData = new FormData();
        formData.append('file', blob, `${encounterName}.json`);

        await axios.post(
          `${API_BASE_URL}/game/${gameName}/encounters/${encounterName}`,
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          }
        );

        // Refresh encounters list
        await dispatch('fetchEncounters', gameName);
        console.log('[ENCOUNTERS] Created encounter:', encounterName);
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.detail || 'Error creating encounter');
        throw error;
      } finally {
        commit('SET_LOADING', false);
      }
    },

    async updateEncounter({ commit, dispatch }, { gameName, encounterName, data }) {
      if (!gameName || !encounterName) {
        return; // silently
      }

      commit('SET_LOADING', true);
      commit('SET_ERROR', null);
      try {
        const formattedJson = JSON.stringify(data, null, 4);
        const blob = new Blob([formattedJson], { type: 'application/json' });
        const formData = new FormData();
        formData.append('file', blob, `${encounterName}.json`);

        await axios.put(
          `${API_BASE_URL}/game/${gameName}/encounters/${encounterName}`,
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          }
        );

        // Refresh encounters list
        await dispatch('fetchEncounters', gameName);
        console.log('[ENCOUNTERS] Updated encounter:', encounterName);
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.detail || 'Error updating encounter');
        throw error;
      } finally {
        commit('SET_LOADING', false);
      }
    },

    async deleteEncounter({ commit, dispatch }, { gameName, encounterName }) {
      if (!gameName || !encounterName) {
        return; // silently
      }

      commit('SET_LOADING', true);
      commit('SET_ERROR', null);
      try {
        await axios.delete(
          `${API_BASE_URL}/game/${gameName}/encounters/${encounterName}`
        );

        // Refresh encounters list
        await dispatch('fetchEncounters', gameName);
        console.log('[ENCOUNTERS] Deleted encounter:', encounterName);
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.detail || 'Error deleting encounter');
        throw error;
      } finally {
        commit('SET_LOADING', false);
      }
    },
  },
  getters: {
    encounters: (state) => state.encounters,
    encounterNames: (state) => Object.keys(state.encounters),
    getEncounterData: (state) => (encounterName) => state.encounters[encounterName],
    currentEncounter: (state) => state.currentEncounter,
    isLoading: (state) => state.loading,
    error: (state) => state.error,
  },
};