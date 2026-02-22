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
          <v-btn icon class="home-btn" @click="goHome">
            <v-icon>mdi-home</v-icon>
          </v-btn>
          <button @click="newFileDialog" class="retro-btn retro-btn--secondary retro-btn--sm">New Game</button>
          <button @click="openFileDialog" class="retro-btn retro-btn--secondary retro-btn--sm">Load Game</button>
          <button @click="save" class="retro-btn retro-btn--secondary retro-btn--sm">Save Game</button>
        </div>
      </div>
    </template>
    
    <!-- Small Screen: Just toolbar row -->
    <template v-else>
      <v-btn icon class="home-btn" @click="goHome">
        <v-icon>mdi-home</v-icon>
      </v-btn>
      <button @click="newFileDialog" class="retro-btn retro-btn--secondary retro-btn--sm">New Game</button>
      <button @click="openFileDialog" class="retro-btn retro-btn--secondary retro-btn--sm">Load Game</button>
      <button @click="save" class="retro-btn retro-btn--secondary retro-btn--sm">Save Game</button>
      <v-spacer></v-spacer>
    </template>
    
    <!-- Dialogs -->
    <GameSelectDialog v-model:dialog="gameSelectDialog" />
    <GameNewDialog v-model:dialog="gameNewDialog" />
    <EncounterNewDialog v-model="encounterNewDialog" />
  </v-app-bar>
</template>

<script>
import { mapActions } from 'vuex';
import GameNewDialog from './GameNewDialog.vue';
import GameSelectDialog from './GameSelectDialog.vue';
import EncounterNewDialog from './EncounterNewDialog.vue';

export default {
  name: 'ApplicationHeader',
  components: {
    GameSelectDialog,
    GameNewDialog,
    EncounterNewDialog,
  },
  data() {
    return {
      windowWidth: window.innerWidth,
      gameSelectDialog: false,
      gameNewDialog: false,
      encounterNewDialog: false,
    };
  },
  computed: {
    isLargeScreen() {
      return this.windowWidth >= 1200;
    },
  },
  mounted() {
    window.addEventListener('resize', this.handleResize);
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.handleResize);
  },
  methods: {
    ...mapActions('game', ['saveGame']),
    
    handleResize() {
      this.windowWidth = window.innerWidth;
    },
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
  font-family: var(--game-font-family-retro, 'Press Start 2P', monospace);
  font-size: 32px;
  color: var(--game-accent-secondary);
  text-shadow: 2px 2px 0 var(--game-accent-primary), 4px 4px 0 rgba(0, 0, 0, 0.5);
  letter-spacing: 2px;
}

.app-header__title-sub {
  font-family: var(--game-font-family-retro, 'Press Start 2P', monospace);
  font-size: 20px;
  color: var(--game-text-secondary);
  text-shadow: 1px 1px 0 rgba(0, 0, 0, 0.5);
}

.app-header__tagline {
  font-family: var(--game-font-family-retro, 'Press Start 2P', monospace);
  font-size: 14px;
  color: var(--game-text-muted);
  text-transform: uppercase;
  letter-spacing: 1px;
  border-left: 2px solid var(--game-accent-primary);
  padding-left: 16px;
  margin-left: 8px;
}

.app-header__version {
  position: absolute;
  right: 16px;
  font-family: var(--game-font-family-retro, 'Press Start 2P', monospace);
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

/* Home Button */
.app-header .home-btn {
  background: rgba(243, 156, 18, 0.15) !important;
  border: 2px solid var(--game-accent-secondary) !important;
  margin-right: var(--game-spacing-md) !important;
}

.app-header .home-btn:hover {
  background: var(--game-accent-secondary) !important;
  box-shadow: 0 0 15px var(--game-accent-secondary) !important;
  transform: scale(1.15) !important;
}

.app-header .home-btn .v-icon {
  color: var(--game-accent-secondary) !important;
  font-size: 28px !important;
}

.app-header .home-btn:hover .v-icon {
  color: var(--game-text-primary) !important;
}
</style>