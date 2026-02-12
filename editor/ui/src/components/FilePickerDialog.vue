<template>
  <v-dialog :model-value="dialog" max-width="600" @click:outside="closeDialog" @update:model-value="updateDialog">
    <v-card class="file-picker-dialog">
      <DialogHeader 
        title="Select a Map" 
        icon="mdi-map"
        @close="closeDialog" 
      />
      <v-card-text class="dialog-content">
        <div class="scrollable-list">
          <ul>
            <li
              v-for="(map, index) in maps"
              :key="index"
              @click="selectMap(map)"
              class="clickable-item"
            >
              {{ map }}
            </li>
          </ul>
        </div>
      </v-card-text>
      <v-card-actions class="dialog-actions">
        <v-spacer></v-spacer>
        <button @click="closeDialog" class="retro-btn retro-btn--secondary retro-btn--sm">
          Cancel
        </button>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import { mapActions, mapGetters } from 'vuex';
import DialogHeader from './DialogHeader.vue';

export default {
  components: { DialogHeader },
  props: {
    dialog: {
      type: Boolean,
      required: true,
    },
  },
  computed: {
    ...mapGetters('maps', ['maps']),
  },
  methods: {
    ...mapActions('maps', ['fetchMaps', 'downloadMap']),

    async loadMaps() {
      await this.fetchMaps();
    },

    async selectMap(map) {
      // Download the selected map content and store it in Vuex
      await this.downloadMap(map);
      this.$router.replace({ name: this.$route.name, params: { mapName: map } });
      this.$emit('update:dialog', false); // Close the dialog
    },

    closeDialog() {
      this.$emit('update:dialog', false); // Close the dialog
    },

    updateDialog(value) {
      this.$emit('update:dialog', value); // Update dialog state in parent
    },
  },
  watch: {
    dialog(value) {
      if (value) {
        this.loadMaps(); // Load maps when dialog opens
      }
    },
  },
};
</script>

<style scoped>
/* Override Vuetify defaults */
.file-picker-dialog :deep(.v-card) {
  background: var(--game-bg-secondary) !important;
  color: var(--game-text-primary) !important;
}

.file-picker-dialog {
  background: var(--game-bg-secondary);
  color: var(--game-text-primary);
  border: 2px solid var(--game-border-highlight);
  border-radius: var(--game-radius-lg);
  box-shadow: var(--game-shadow-lg);
}


.dialog-content {
  padding: var(--game-spacing-lg);
  background: var(--game-bg-secondary);
}

/* Scrollable List */
.scrollable-list {
  min-height: 300px;
  max-height: 400px;
  overflow-y: auto;
  background: var(--game-bg-primary);
  border: 2px solid var(--game-border-color);
  border-radius: var(--game-radius-md);
  padding: var(--game-spacing-sm);
  margin: 0;
  box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.4);
}

/* Scrollbar Styling */
.scrollable-list::-webkit-scrollbar {
  width: 12px;
}

.scrollable-list::-webkit-scrollbar-track {
  background: var(--game-bg-tertiary);
  border-radius: var(--game-radius-sm);
}

.scrollable-list::-webkit-scrollbar-thumb {
  background: var(--game-accent-primary);
  border-radius: var(--game-radius-sm);
  border: 2px solid var(--game-bg-tertiary);
}

.scrollable-list::-webkit-scrollbar-thumb:hover {
  background: var(--game-accent-tertiary);
  box-shadow: 0 0 8px var(--game-accent-primary);
}

.scrollable-list ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

/* List Items - 8-Bit Style */
.scrollable-list li {
  padding: var(--game-spacing-md);
  cursor: pointer;
  background: var(--game-bg-secondary);
  border: 2px solid var(--game-border-color);
  border-radius: var(--game-radius-sm);
  margin-bottom: var(--game-spacing-sm);
  color: var(--game-text-primary);
  font-family: var(--game-font-family-mono);
  font-size: var(--game-font-size-md);
  font-weight: 600;
  transition: all var(--game-transition-fast);
  text-shadow: 1px 1px 0px rgba(0, 0, 0, 0.5);
}

.scrollable-list li:hover {
  background: var(--game-input-hover);
  border-color: var(--game-accent-primary);
  color: var(--game-accent-secondary);
  transform: translateX(5px);
  box-shadow: -3px 0 0 var(--game-accent-primary), 
              0 0 15px rgba(233, 69, 96, 0.3);
  text-shadow: 1px 1px 0px rgba(0, 0, 0, 0.8),
               0 0 8px var(--game-accent-secondary);
}

.scrollable-list li:active {
  transform: translateX(3px);
  box-shadow: -2px 0 0 var(--game-accent-primary);
}

.dialog-actions {
  padding: var(--game-spacing-lg);
  border-top: 1px solid var(--game-border-color);
  background: var(--game-bg-tertiary);
}

.dialog-actions .retro-btn {
  margin-left: var(--game-spacing-md);
}
</style>