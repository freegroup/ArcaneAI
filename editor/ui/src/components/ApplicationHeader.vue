<template>
  <v-app-bar class="app-header" :height="isLargeScreen ? 128 : 48">
    <!-- Large Screen: Two rows (Title + Toolbar) -->
    <template v-if="isLargeScreen">
      <div class="app-header__wrapper">
        <!-- Top Row: Branding -->
        <div class="app-header__branding">
          <h1 class="app-header__title">
            <span class="app-header__title-main">ArcaneAI</span>
            <span class="app-header__title-sub">Studio</span>
          </h1>
          <span class="app-header__tagline">Craft AI-Powered Text Adventures</span>
          <span class="app-header__version">v0.1</span>
        </div>
        
        <!-- Bottom Row: Toolbar -->
        <div class="app-header__toolbar">
          <RetroButton @click="newFileDialog" variant="secondary">New Game</RetroButton>
          <RetroButton @click="openFileDialog" variant="secondary">Load Game</RetroButton>
          <RetroButton @click="save" variant="secondary">
            Save Game<span v-if="hasUnsavedChanges" class="unsaved-indicator">*</span>
          </RetroButton>
        </div>
      </div>
    </template>
    
    <!-- Small Screen: Just toolbar row -->
    <template v-else>
      <RetroButton @click="newFileDialog" variant="secondary">New Game</RetroButton>
      <RetroButton @click="openFileDialog" variant="secondary">Load Game</RetroButton>
      <RetroButton @click="save" variant="secondary">
        Save Game<span v-if="hasUnsavedChanges" class="unsaved-indicator">*</span>
      </RetroButton>
      <v-spacer></v-spacer>
    </template>
    
    <!-- Dialogs -->
    <GameSelectDialog v-model:dialog="gameSelectDialog" />
    <GameNewDialog v-model:dialog="gameNewDialog" />
    <EncounterNewDialog v-model="encounterNewDialog" />
  </v-app-bar>
</template>

<script>
import { mapActions, mapGetters } from 'vuex';
import GameNewDialog from './GameNewDialog.vue';
import GameSelectDialog from './GameSelectDialog.vue';
import EncounterNewDialog from './EncounterNewDialog.vue';
import RetroButton from './RetroButton.vue';

export default {
  name: 'ApplicationHeader',
  components: {
    GameSelectDialog,
    GameNewDialog,
    EncounterNewDialog,
    RetroButton,
  },
  data() {
    return {
      gameSelectDialog: false,
      gameNewDialog: false,
      encounterNewDialog: false,
    };
  },
  computed: {
    ...mapGetters('game', ['hasUnsavedChanges']),
    
    /**
     * Use Vuetify's built-in breakpoint system instead of manual windowWidth tracking.
     * mdAndUp (>= 960px) is typically where we start showing the full header on desktop/laptops.
     */
    isLargeScreen() {
      return this.$vuetify.display.mdAndUp;
    },
  },
  methods: {
    ...mapActions('game', ['saveGame']),
    
    goHome() {
      this.$router.push('/');
    },
    newFileDialog() {
      this.gameNewDialog = true;
    },
    openFileDialog() {
      this.gameSelectDialog = true;
    },
    save() {
      this.saveGame();
    },
    newEncounterDialog() {
      this.encounterNewDialog = true;
    },
  },
};
</script>

<style>
/* App Header - Main container */
.app-header.v-toolbar {
  background: linear-gradient(180deg, var(--game-bg-primary) 0%, var(--game-bg-tertiary) 100%) !important;
  border-bottom: 3px solid var(--game-accent-primary) !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.6) !important;
}

.app-header .v-toolbar__content {
  padding: 0 !important;
  height: 100% !important;
}

/* Wrapper for large screen layout */
.app-header__wrapper {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
}

/* Branding Row (Title) */
.app-header__branding {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 16px;
  height: 80px;
  padding-left: 16px;
  border-bottom: 2px solid var(--game-accent-secondary);
  background: linear-gradient(180deg, rgba(243, 156, 18, 0.1) 0%, transparent 100%);
  position: relative;
}

.app-header__title {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin: 0;
}

.app-header__title-main {
  font-family: var(--game-font-family-retro);
  font-size: 48px;
  color: var(--game-accent-secondary);
  letter-spacing: 6px;
}

.app-header__title-sub {
  font-family: var(--game-font-family-retro);
  font-size: 48px;
  letter-spacing: 4px;
  color: var(--game-text-secondary);
}

.app-header__tagline {
  font-family: var(--game-font-family-retro);
  font-size: 24px;
  color: var(--game-text-muted);
  text-transform: uppercase;
  letter-spacing: 4px;
  border-left: 2px solid var(--game-accent-primary);
  padding-left: 16px;
  margin-left: 8px;
}

.app-header__version {
  position: absolute;
  right: 16px;
  font-family: var(--game-font-family-retro);
  font-size: 7px;
  color: var(--game-text-muted);
  opacity: 0.6;
}

/* Toolbar Row */
.app-header__toolbar {
  display: flex;
  align-items: center;
  height: 48px;
  padding: 0 8px;
}

.app-header__toolbar .retro-btn {
  margin: 0 var(--game-spacing-sm) !important;
}

/* Unsaved changes indicator */
.unsaved-indicator {
  color: var(--game-accent-secondary, #f39c12);
  font-weight: bold;
  margin-left: 2px;
  animation: pulse-indicator 1.5s ease-in-out infinite;
}

@keyframes pulse-indicator {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>
