<template>
  <v-app-bar border dark >
    <v-btn icon>
      <v-icon>mdi-home</v-icon>
    </v-btn>
    <v-btn text @click="newFileDialog">New Game</v-btn>
    <v-btn text @click="openFileDialog">Load Game</v-btn>
    <v-btn text @click="save">Save Game</v-btn>
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

/* Override Vuetify App Bar */
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

/* Text Buttons (NEW, LOAD, SAVE) */
.v-toolbar .v-btn:not(.v-btn--icon) {
  font-family: var(--game-font-family-retro) !important;
  font-size: 16px !important;
  font-weight: 700 !important;
  text-transform: uppercase !important;
  letter-spacing: 2px !important;
  color: var(--game-text-primary) !important;
  background: rgba(233, 69, 96, 0.1) !important;
  border: 2px solid transparent !important;
  margin: 0 4px !important;
  padding: 0 20px !important;
  text-shadow: 1px 1px 0px rgba(0, 0, 0, 0.8) !important;
  transition: all var(--game-transition-fast) !important;
}

.v-toolbar .v-btn:not(.v-btn--icon):hover {
  background: rgba(233, 69, 96, 0.3) !important;
  border-color: var(--game-accent-primary) !important;
  color: var(--game-accent-secondary) !important;
  text-shadow: 1px 1px 0px rgba(0, 0, 0, 0.8),
               0 0 8px var(--game-accent-secondary) !important;
  transform: translateY(-2px) !important;
  box-shadow: 0 4px 8px rgba(233, 69, 96, 0.4) !important;
}

.v-toolbar .v-btn:not(.v-btn--icon):active {
  transform: translateY(0px) !important;
  box-shadow: 0 2px 4px rgba(233, 69, 96, 0.6) !important;
}
</style>
