<template>
  <v-app-bar border dark class="app-toolbar">
    <v-btn icon class="home-btn">
      <v-icon>mdi-home</v-icon>
    </v-btn>
    
    <button @click="newFileDialog" class="retro-btn retro-btn--secondary retro-btn--sm">New Game</button>
    <button @click="openFileDialog" class="retro-btn retro-btn--secondary retro-btn--sm">Load Game</button>
    <button @click="save" class="retro-btn retro-btn--secondary retro-btn--sm">Save Game</button>
    
    <v-spacer></v-spacer>

    <FilePickerDialog v-model:dialog="filePickerDialog" />
    <FileNewDialog    v-model:dialog="fileNewDialog" />
  </v-app-bar>
</template>

<script>
import { mapActions } from 'vuex';
import FileNewDialog from './FileNewDialog.vue';
import FilePickerDialog from './FilePickerDialog.vue';

export default {
  components: {
    FilePickerDialog,
    FileNewDialog,
  },
  data() {
    return {
      filePickerDialog: false,
      fileNewDialog: false,
    };
  },
  methods: {
    ...mapActions('maps', ['saveMap']),
    
    newFileDialog() {
      this.fileNewDialog = true;
    },
    
    openFileDialog() {
      this.filePickerDialog = true;
    },
    
    save() {
      console.log("Save Map");
      this.saveMap();
    },
  },
};
</script>

<style>
/* Remove scoped to ensure styles apply */

/* Override Vuetify App Bar - Fixed height of 48px */
.v-toolbar {
  background: linear-gradient(135deg, var(--game-bg-tertiary) 0%, #0a0a14 100%) !important;
  border-bottom: 3px solid var(--game-accent-primary) !important;
  border-top: 2px solid var(--game-accent-secondary) !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.6), 
              inset 0 -2px 0 rgba(0, 0, 0, 0.4) !important;
}

.v-toolbar__content {
  background: transparent !important;
}

/* Home Icon Button */
.v-toolbar .v-btn[icon],
.v-toolbar .v-btn--icon {
  background: rgba(243, 156, 18, 0.15) !important;
  border: 2px solid var(--game-accent-secondary) !important;
  margin-right: var(--game-spacing-md) !important;
  transition: all var(--game-transition-fast) !important;
}

.v-toolbar .v-btn[icon]:hover,
.v-toolbar .v-btn--icon:hover {
  background: var(--game-accent-secondary) !important;
  border-color: var(--game-accent-tertiary) !important;
  box-shadow: 0 0 15px var(--game-accent-secondary) !important;
  transform: scale(1.15) !important;
}

.v-toolbar .v-btn[icon] .v-icon,
.v-toolbar .v-btn--icon .v-icon {
  color: var(--game-accent-secondary) !important;
  font-size: 28px !important;
  filter: drop-shadow(0 0 6px var(--game-accent-secondary));
}

.v-toolbar .v-btn[icon]:hover .v-icon,
.v-toolbar .v-btn--icon:hover .v-icon {
  color: var(--game-text-primary) !important;
  filter: drop-shadow(0 0 10px rgba(255, 255, 255, 0.8));
}

/* Toolbar Retro Buttons */
.app-toolbar .retro-btn {
  margin: 0 var(--game-spacing-sm) !important;
}
</style>