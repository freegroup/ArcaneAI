/**
 * Encounters Store - Simplified (Overlay Pattern)
 * 
 * Encounters are derived from views with viewType='encounter'.
 * This store only manages encounter metadata (name, description) from the API.
 * Layout data comes from the views store.
 */
import axios from 'axios';

const API_BASE_URL = process.env.VUE_APP_API_BASE_URL;

export default {
  namespaced: true,
  
  state: {
    // Map of encounter names to their config: { '001_go': { name: 'Enter the Room', description: '...' } }
    encounters: {},
    currentEncounterName: null,
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
  },
  
  actions: {
    async initialize() {
      // Placeholder for future initialization
    },

    /**
     * Fetch all encounters for a game.
     * The API now returns encounter names derived from views/encounter_*.json files.
     */
    async fetchEncounters({ commit }, gameName) {
      if (!gameName || gameName.length === 0) {
        return;
      }

      commit('SET_LOADING', true);
      commit('SET_ERROR', null);
      
      try {
        // Get list of encounter names
        const namesResponse = await axios.get(`${API_BASE_URL}/game/${gameName}/encounters`);
        const encounterNames = namesResponse.data;
        
        // Load config for each encounter
        const encountersMap = {};
        for (const name of encounterNames) {
          try {
            const configResponse = await axios.get(`${API_BASE_URL}/game/${gameName}/encounters/${name}`);
            encountersMap[name] = configResponse.data;
          } catch (error) {
            console.warn(`[ENCOUNTERS] Error loading config for ${name}:`, error);
            encountersMap[name] = { name, description: '' };
          }
        }
        
        commit('SET_ENCOUNTERS', encountersMap);
        console.log('[ENCOUNTERS] Loaded encounters for game:', gameName, encountersMap);
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.detail || 'Error fetching encounters');
        console.error('[ENCOUNTERS] Error loading encounters:', error);
      } finally {
        commit('SET_LOADING', false);
      }
    },

    /**
     * Set the current encounter by name
     */
    setCurrentEncounter({ commit }, encounterName) {
      commit('SET_CURRENT_ENCOUNTER_NAME', encounterName);
      console.log('[ENCOUNTERS] Set current encounter:', encounterName);
    },

    /**
     * Clear the current encounter
     */
    clearCurrentEncounter({ commit }) {
      commit('SET_CURRENT_ENCOUNTER_NAME', null);
      console.log('[ENCOUNTERS] Cleared current encounter');
    },
  },
  
  getters: {
    encounters: (state) => state.encounters,
    encounterNames: (state) => Object.keys(state.encounters),
    getEncounterConfig: (state) => (encounterName) => state.encounters[encounterName],
    currentEncounterName: (state) => state.currentEncounterName,
    currentEncounterConfig: (state) => {
      if (!state.currentEncounterName) return null;
      return state.encounters[state.currentEncounterName] || null;
    },
    isLoading: (state) => state.loading,
    error: (state) => state.error,
  },
};