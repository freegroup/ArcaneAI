<template>
  <div v-if="showViewProperties" class="property-view">
    <!-- View Name Section -->
    <div class="field-group">
      <label>{{ isWorldView ? 'View' : 'Encounter' }} Name</label>
      <input
        id="encounterName"
        type="text"
        v-model="localName"
        :readonly="isWorldView"
        :class="{ 'readonly-name': isWorldView }"
        @input="!isWorldView && debouncedSaveName()"
        placeholder="Enter encounter name..."
      />
    </div>

    <!-- Description Section -->
    <div class="field-group">
      <label>Description</label>
      <textarea
        v-model="localDescription"
        placeholder="Describe what this view represents..."
        rows="4"
        @input="saveDescription"
      />
    </div>
    
    <!-- Todo List Section (Extracted to Component) -->
    <TodoManager />
  </div>
</template>

<script>
import { mapGetters } from 'vuex';
import { MessageTypes } from '../../public/shared/SharedConstants.js';
import TodoManager from '../components/TodoManager.vue';

export default {
  name: 'EncounterPropertyView',
  
  components: {
    TodoManager
  },
  
  props: {
    draw2dFrame: {
      type: Object,
      default: null
    }
  },
  
  data() {
    return {
      localName: '',
      localDescription: '',
      jsonData: null,  // Track selected element data (null = nothing selected)
      saveNameTimeout: null,  // Debounce timer for name saving
    };
  },
  
  computed: {
    ...mapGetters('views', ['currentView']),
    
    /**
     * Show view properties when:
     * - A view is loaded (currentView exists)
     * - Nothing is selected on the canvas (jsonData is null/empty)
     */
    showViewProperties() {
      return this.currentView && !this.jsonData;
    },
    
    /**
     * Check if current view is the world view (readonly name)
     */
    isWorldView() {
      const viewId = this.currentView?.viewId || this.currentView?.id;
      return viewId === 'world';
    }
  },
  
  watch: {
    currentView: {
      immediate: true,
      handler(newView) {
        if (newView?.encounterConfig?.name !== undefined) {
          this.localName = newView.encounterConfig.name;
        } else {
          // Default name based on view type
          const viewId = newView?.viewId || newView?.id;
          this.localName = viewId === 'world' ? 'World' : '';
        }
        if (newView?.encounterConfig?.description !== undefined) {
          this.localDescription = newView.encounterConfig.description;
        } else {
          this.localDescription = '';
        }
      }
    }
  },
  
  methods: {
    /**
     * Debounced save name - waits 50ms after user stops typing
     */
    debouncedSaveName() {
      if (this.saveNameTimeout) {
        clearTimeout(this.saveNameTimeout);
      }
      this.saveNameTimeout = setTimeout(() => {
        this.saveName();
      }, 50);
    },
    
    /**
     * Save name - triggers full rename including file rename and navigation update
     */
    async saveName() {
      const trimmedName = this.localName.trim();
      const originalName = this.currentView?.encounterConfig?.name || '';
      
      // Only rename if name actually changed
      if (!trimmedName || trimmedName === originalName) {
        // Reset to original name if empty
        if (!trimmedName) {
          this.localName = originalName;
        }
        return;
      }
      
      try {
        const viewId = this.currentView.viewId || this.currentView.id;
        const gameName = this.$route.params.gameName;
        
        // Call renameView action which handles file rename
        const newViewId = await this.$store.dispatch('views/renameView', {
          gameName,
          viewId,
          newName: trimmedName
        });
        
        // Refresh encounters to update navigation
        await this.$store.dispatch('encounters/fetchEncounters', gameName);
        
        // Navigate to new URL if viewId changed
        if (newViewId && newViewId !== viewId) {
          const newEncounterId = newViewId.replace('encounter_', '');
          this.$router.replace(`/game/${gameName}/encounter/${newEncounterId}`);
        }
      } catch (error) {
        console.error('Failed to rename encounter:', error);
        // Reset to original name on error
        this.localName = originalName;
      }
    },
    
    /**
     * Save description to store
     */
    saveDescription() {
      this.updateEncounterConfig({ description: this.localDescription });
    },
    
    /**
     * Helper to update encounterConfig
     */
    updateEncounterConfig(updates) {
      if (!this.currentView) return;
      
      const currentConfig = this.currentView.encounterConfig || {};
      const newConfig = { ...currentConfig, ...updates };
      
      this.$store.commit('views/PATCH_ENCOUNTER_CONFIG', {
        viewId: this.currentView.viewId || this.currentView.id,
        encounterConfig: newConfig
      });
    },
    
    /**
     * Handle canvas selection messages
     */
    handleMessage(event) {
      if (event.origin !== window.location.origin) return;
      
      const message = event.data;
      
      if (message.event === MessageTypes.C2V_SELECT) {
        this.jsonData = message.data;
      } else if (message.event === MessageTypes.C2V_UNSELECT) {
        this.jsonData = null;
      }
    }
  },
  
  mounted() {
    window.addEventListener('message', this.handleMessage);
  },
  
  beforeUnmount() {
    window.removeEventListener('message', this.handleMessage);
    if (this.saveNameTimeout) {
      clearTimeout(this.saveNameTimeout);
    }
  }
};
</script>

<style scoped>
.property-view {
  height: 100%;
  overflow: auto;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

.property-view textarea {
  resize: vertical;
}

/* Readonly name style for World view */
.property-view input#encounterName.readonly-name {
  cursor: default;
  pointer-events: none;
}

/* Field Group Container */
.field-group {
  display: flex;
  flex-direction: column;
}
</style>
