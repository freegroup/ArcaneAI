import axios from 'axios';

const API_BASE_URL = process.env.VUE_APP_API_BASE_URL;

export default {
  namespaced: true,
  state: {
    files: [],
    loading: false,
    error: null,
    currentSoundUrl: null,
  },
  mutations: {
    SET_FILES(state, files) {
      state.files = files;
    },
    SET_LOADING(state, isLoading) {
      state.loading = isLoading;
    },
    SET_ERROR(state, error) {
      state.error = error;
    },
    SET_CURRENT_SOUND_URL(state, url) {
      state.currentSoundUrl = url;
    },
  },
  actions: {
    async initialize({ dispatch }) {
      // Call fetchSounds to initialize the sound files on app start
      await dispatch('fetchSounds');
    },

    async fetchSounds({ commit }) {
      commit('SET_LOADING', true)
      commit('SET_ERROR', null)
      try {
        const response = await axios.get(`${API_BASE_URL}/sounds/`)
        const sortedFiles = response.data.sort((a, b) => a.localeCompare(b));
        
        commit('SET_FILES', sortedFiles);
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.detail || 'Error fetching sounds')
      } finally {
        commit('SET_LOADING', false)
      }
    },

    async downloadSound({ commit }, fileName) {
      commit('SET_LOADING', true);
      commit('SET_ERROR', null);
      try {
        const response = await axios.get(`${API_BASE_URL}/sounds/${fileName}`, {
          responseType: 'blob',
        });
        
        // Convert the blob into an object URL
        const blob = new Blob([response.data], { type: 'audio/mpeg' });
        const url = URL.createObjectURL(blob);
        commit('SET_CURRENT_SOUND_URL', url);  

      } catch (error) {
        commit('SET_ERROR', error.response?.data?.detail || 'Error downloading file');
        throw error;
      } finally {
        commit('SET_LOADING', false);
      }
    },

  },
  getters: {
    files: (state) => state.files,
    isLoading: (state) => state.loading,
    error: (state) => state.error,
    currentSoundUrl: (state) => state.currentSoundUrl,
  },
};
