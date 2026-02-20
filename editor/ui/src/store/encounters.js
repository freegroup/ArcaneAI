import axios from 'axios';

const API_BASE_URL = process.env.VUE_APP_API_BASE_URL;

export default {
  namespaced: true,
  state: {
    encounters: [],
    currentEncounterName: null,  // Name des aktuell bearbeiteten Encounters
    loading: false,
    error: null,
  },
  mutations: {
    SET_ENCOUNTERS(state, encounters) {
      state.encounters = encounters;
    },
    SET_CURRENT_ENCOUNTER_NAME(state, encounterName) {
      state.currentEncounterName = encounterName;
    },
    SET_LOADING(state, isLoading) {
      state.loading = isLoading;
    },
    SET_ERROR(state, error) {
      state.error = error;
    },
    UPDATE_ENCOUNTER_DIAGRAM(state, { encounterName, diagram }) {
      if (state.encounters[encounterName]) {
        state.encounters[encounterName].diagram = diagram;
      }
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

    // Set the current encounter by name (used when navigating to CanvasEncounter)
    setCurrentEncounter({ commit }, encounterName) {
      commit('SET_CURRENT_ENCOUNTER_NAME', encounterName);
      console.log('[ENCOUNTERS] Set current encounter:', encounterName);
    },

    // Clear the current encounter (used when leaving CanvasEncounter)
    clearCurrentEncounter({ commit }) {
      commit('SET_CURRENT_ENCOUNTER_NAME', null);
      console.log('[ENCOUNTERS] Cleared current encounter');
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

    updateEncounterDiagram({ commit }, { encounterName, diagram }) {
      commit('UPDATE_ENCOUNTER_DIAGRAM', { encounterName, diagram });
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
    
    // Name des aktuellen Encounters
    currentEncounterName: (state) => state.currentEncounterName,
    
    // Komplettes JSON des aktuellen Encounters (aus encounters Map)
    currentEncounter: (state) => {
      if (!state.currentEncounterName) return null;
      return state.encounters[state.currentEncounterName] || null;
    },
    
    // Diagram des aktuellen Encounters (Shortcut)
    currentEncounterDiagram: (state) => {
      if (!state.currentEncounterName) return null;
      const encounter = state.encounters[state.currentEncounterName];
      return encounter?.diagram || null;
    },
    
    isLoading: (state) => state.loading,
    error: (state) => state.error,
  },
};