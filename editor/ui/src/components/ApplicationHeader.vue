<template>
  <v-app-bar class="app-header" :height="headerHeight">
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
          <span class="app-header__spacer"></span>
          <ThemeSelector />
        </div>

        <!-- Bottom Row: Toolbar (only when game loaded) -->
        <div v-if="showToolbar" class="app-header__toolbar">
          <ThemedButton @click="$emit('new-game')" variant="secondary">New Game</ThemedButton>
          <ThemedButton @click="$emit('load-game')" variant="secondary">Load Game</ThemedButton>
          <ThemedButton @click="save" variant="secondary">
            Save Game<span v-if="hasUnsavedChanges" class="unsaved-indicator">*</span>
          </ThemedButton>
        </div>
      </div>
    </template>

    <!-- Small Screen: Just toolbar row -->
    <template v-else>
      <template v-if="showToolbar">
        <ThemedButton @click="$emit('new-game')" variant="secondary">New Game</ThemedButton>
        <ThemedButton @click="$emit('load-game')" variant="secondary">Load Game</ThemedButton>
        <ThemedButton @click="save" variant="secondary">
          Save Game<span v-if="hasUnsavedChanges" class="unsaved-indicator">*</span>
        </ThemedButton>
      </template>
      <v-spacer></v-spacer>
      <ThemeSelector />
    </template>
  </v-app-bar>
</template>

<script>
import { mapActions, mapGetters } from 'vuex';
import ThemedButton from './ThemedButton.vue';
import ThemeSelector from './ThemeSelector.vue';

export default {
  name: 'ApplicationHeader',
  components: {
    ThemedButton,
    ThemeSelector,
  },
  emits: ['new-game', 'load-game'],
  props: {
    showToolbar: {
      type: Boolean,
      default: true,
    },
  },
  computed: {
    ...mapGetters('game', ['hasUnsavedChanges']),

    isLargeScreen() {
      return this.$vuetify.display.mdAndUp;
    },
    headerHeight() {
      if (!this.isLargeScreen) return 48;
      return this.showToolbar ? 128 : 72;
    },
  },
  methods: {
    ...mapActions('game', ['saveGame']),

    goHome() {
      this.$router.push('/');
    },
    save() {
      this.saveGame();
    },
  },
};
</script>

<style>
/* Structural layout only — visual styles in theme files */

.app-header .v-toolbar__content {
  height: 100% !important;
}

.app-header__wrapper {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
}

.app-header__branding {
  display: flex;
  align-items: center;
}

.app-header__spacer {
  flex: 1;
}

.app-header__title {
  display: flex;
  align-items: baseline;
}

.app-header__toolbar {
  display: flex;
  align-items: center;
}

/* Unsaved changes indicator — animation is behavioral */
.unsaved-indicator {
  animation: pulse-indicator 1.5s ease-in-out infinite;
}

@keyframes pulse-indicator {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>
