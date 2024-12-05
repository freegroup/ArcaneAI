import axios from 'axios';
import yaml from 'js-yaml';

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
      commit('SET_MAP_DIAGRAM', data);
    },

    async saveMap({ commit, state }) {
      commit('SET_LOADING', true);
      commit('SET_ERROR', null);
      try {
        const formattedJson = JSON.stringify({
          "config": state.mapConfig,
          "diagram": state.mapDiagram
        }, null, 4);

        let blob = new Blob([formattedJson], { type: 'application/json' });
        let formData = new FormData();
        formData.append('file', blob, state.mapName + ".json");

        // Send PUT request to backend
        await axios.put(`${API_BASE_URL}/maps/`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });

        // Find the starting state shape
        const startStateShape = state.mapDiagram.find(
          (shape) => shape.type === "StateShape" && shape.stateType === "START"
        );
        const startStateName = startStateShape ? startStateShape.name : null;
        
        // Prepare data for the YAML file
        const stateShapes = state.mapDiagram
          .filter((item) => item.type === "StateShape")
          .map((shape) => ({
            name: shape.name,
            metadata: {
              // kopiere erstmal alles...
              ...shape.userData,
              //...und ein paar Felder benötigen ein "trim"
              system_prompt: (shape.userData?.system_prompt ?? "").trim(),
              ambient_sound: shape.userData?.ambient_sound?.trim(),
              state_type:  shape.stateType?.toLowerCase()
            },
          }));

        const trans = state.mapDiagram
          .filter((shape) => shape.type === "StateShape" && shape.trigger && shape.trigger.length > 0)
          .flatMap((shape) => 
            shape.trigger.map((trigger) => ({
              trigger: trigger.id.replace(/-/g, "_"),
              source: shape.name,
              dest: shape.name,
              metadata: {
                name: trigger.name,
                system_prompt: trigger.system_prompt || "",
                description: trigger.description || "",
                sound_effect: trigger.sound_effect || "",
                sound_effect_volume: trigger.sound_effect_volume || 100,
                sound_effect_duration: trigger.sound_effect_duration,
                conditions: trigger.conditions || [],
                actions: trigger.actions || []
              }
            }))
          );

        const trans2 = state.mapDiagram
          .filter((item) => item.type === "TriggerConnection")
          .map((triggerConnection) => ({
            trigger: triggerConnection.id.replace(/-/g, "_"),
            source: triggerConnection.source.name,
            dest: triggerConnection.target.name,
            metadata: {
              name: triggerConnection.name,
              system_prompt: triggerConnection.userData?.system_prompt || "",
              description: triggerConnection.userData?.description || "",
              sound_effect: triggerConnection.userData?.sound_effect || "",
              sound_effect_volume: triggerConnection.userData?.sound_effect_volume || 100,
              sound_effect_duration: triggerConnection.userData?.sound_effect_duration,
              conditions: triggerConnection.userData?.conditions || [],
              actions: triggerConnection.userData?.actions || []
            }
          }));


        // Transform inventory items to the specified object format
        const formattedInventory = {};
        state.mapConfig.inventory.forEach((item) => {
          let formattedValue;
          if (item.type === 'boolean') {
            formattedValue = item.value === 'true' || item.value === true;
          } else if (item.type === 'integer') {
            formattedValue = parseInt(item.value, 10);
          } else {
            formattedValue = item.value;
          }
          formattedInventory[item.key] = formattedValue;
        });

        
        let formatedYaml = yaml.dump({
          initial: startStateName,
          metadata: {
            ...state.mapConfig,
            inventory: formattedInventory // Use the formatted inventory here
          },
          states: stateShapes,
          transitions: [...trans, ...trans2]
          })
        blob = new Blob([formatedYaml], { type: 'application/json' });
        formData = new FormData();
        formData.append('file', blob, state.mapName + ".yaml");
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
  },
};
