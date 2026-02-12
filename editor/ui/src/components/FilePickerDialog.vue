<template>
    <v-dialog :model-value="dialog" max-width="600" @click:outside="closeDialog" @update:model-value="updateDialog">
      <v-card>
        <v-card-title class="headline">
          <v-icon class="title-icon">mdi-map</v-icon>
          Select a Map
          <v-spacer></v-spacer>
          <button @click="closeDialog" class="retro-btn retro-btn--icon">
            ✕
          </button>
        </v-card-title>
        <v-card-text>
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
  
  export default {
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
  
<style>
/* 8-Bit Retro Game Style für File Picker Dialog */

/* Vuetify Card Overrides */
.v-dialog .v-card {
  background: var(--game-bg-secondary) !important;
  border: 3px solid var(--game-accent-primary) !important;
  border-radius: var(--game-radius-lg) !important;
  box-shadow: 0 0 30px rgba(233, 69, 96, 0.4), 
              inset 0 0 20px rgba(0, 0, 0, 0.3) !important;
}

/* Card Title - Retro Style */
.v-dialog .v-card-title {
  background: linear-gradient(135deg, var(--game-bg-tertiary) 0%, #0a0a14 100%) !important;
  color: var(--game-accent-secondary) !important;
  font-family: var(--game-font-family-retro) !important;
  font-size: 18px !important;
  text-transform: uppercase !important;
  letter-spacing: 2px !important;
  padding: var(--game-spacing-lg) !important;
  border-bottom: 3px solid var(--game-accent-primary) !important;
  border-top: 2px solid var(--game-accent-secondary) !important;
  text-shadow: 2px 2px 0px rgba(0, 0, 0, 0.8), 
               0 0 10px var(--game-accent-secondary) !important;
  box-shadow: inset 0 -2px 0 rgba(0, 0, 0, 0.4) !important;
  display: flex !important;
  align-items: center !important;
  gap: var(--game-spacing-sm) !important;
}

/* Title Icon with Pulse Animation */
.v-dialog .v-card-title .title-icon {
  color: var(--game-accent-secondary);
  font-size: 32px;
  filter: drop-shadow(0 0 8px var(--game-accent-secondary));
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    filter: drop-shadow(0 0 8px var(--game-accent-secondary));
  }
  50% {
    transform: scale(1.05);
    filter: drop-shadow(0 0 12px var(--game-accent-secondary));
  }
}


/* Card Text */
.v-dialog .v-card-text {
  background: var(--game-bg-secondary) !important;
  color: var(--game-text-primary) !important;
  padding: var(--game-spacing-lg) !important;
}

/* Scrollable List */
.scrollable-list {
  min-height: 300px;
  max-height: 400px;
  overflow-y: auto;
  background: var(--game-bg-primary) !important;
  border: 2px solid var(--game-border-color) !important;
  border-radius: var(--game-radius-md) !important;
  padding: var(--game-spacing-sm) !important;
  margin: 0;
  box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.4) !important;
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
  padding: var(--game-spacing-md) !important;
  cursor: pointer;
  background: var(--game-bg-secondary) !important;
  border: 2px solid var(--game-border-color) !important;
  border-radius: var(--game-radius-sm) !important;
  margin-bottom: var(--game-spacing-sm) !important;
  color: var(--game-text-primary) !important;
  font-family: var(--game-font-family-mono) !important;
  font-size: var(--game-font-size-md) !important;
  font-weight: 600 !important;
  transition: all var(--game-transition-fast) !important;
  text-shadow: 1px 1px 0px rgba(0, 0, 0, 0.5) !important;
}

.scrollable-list li:hover {
  background: var(--game-input-hover) !important;
  border-color: var(--game-accent-primary) !important;
  color: var(--game-accent-secondary) !important;
  transform: translateX(5px) !important;
  box-shadow: -3px 0 0 var(--game-accent-primary), 
              0 0 15px rgba(233, 69, 96, 0.3) !important;
  text-shadow: 1px 1px 0px rgba(0, 0, 0, 0.8),
               0 0 8px var(--game-accent-secondary) !important;
}

.scrollable-list li:active {
  transform: translateX(3px) !important;
  box-shadow: -2px 0 0 var(--game-accent-primary) !important;
}

/* Card Actions */
.v-dialog .v-card-actions {
  background: var(--game-bg-tertiary) !important;
  padding: var(--game-spacing-lg) !important;
  border-top: 1px solid var(--game-border-color) !important;
}

/* Dialog Actions */
.dialog-actions {
  background: var(--game-bg-tertiary) !important;
  padding: var(--game-spacing-lg) !important;
  border-top: 1px solid var(--game-border-color) !important;
}
</style>
  