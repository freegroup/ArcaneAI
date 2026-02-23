<template>
  <v-app id="app">
    <application-header />

    <!-- Navigation Drawer -->
    <v-navigation-drawer
      permanent
      :rail="isCompact"
      :width="drawerWidth"
      class="nav-drawer"
    >
      <!-- Toggle button -->
      <v-list-item 
        @click="toggleDrawerCompact" 
        class="nav-drawer__toggle"
      >
        <template v-slot:prepend>
          <v-icon :icon="isCompact ? 'mdi-chevron-right' : 'mdi-chevron-left'"></v-icon>
        </template>
      </v-list-item>

      <!-- Game Name Display -->
      <div v-if="!isCompact && currentGameName" class="nav-drawer__game-name">
        <span class="nav-drawer__game-label">{{ currentGameName }}</span>
      </div>

      <v-divider v-if="!isCompact"></v-divider>

      <v-list density="compact" class="nav-drawer__list">
        <!-- Regular navigation items -->
        <v-list-item
          v-for="item in navigationItems.filter(i => i.title !== 'Game Map')"
          :key="item.title"
          :to="item.route($route.params.gameName)"
          :prepend-icon="item.icon"
          :title="isCompact ? undefined : item.title"
          class="nav-drawer__item"
        >
        </v-list-item>

        <!-- Game Map Header -->
        <template v-if="!isCompact && $route.params.gameName">
          <v-list-item
            prepend-icon="mdi-state-machine"
            class="nav-drawer__item nav-drawer__header nav-drawer__header--clickable"
          >
            <template v-slot:prepend>
              <v-icon icon="mdi-state-machine"></v-icon>
            </template>
            <v-list-item-title class="nav-drawer__header-title">Game Map</v-list-item-title>
            <template v-slot:append>
              <RetroButton
                @click.stop="openAddEncounterDialog"
                size="icon"
                class="nav-drawer__add-btn"
                title="Add new encounter"
              >+</RetroButton>
            </template>
          </v-list-item>

          <!-- World Item -->
          <v-list-item
            :to="`/game/${$route.params.gameName}/world`"
            prepend-icon="mdi-earth"
            title="World"
            class="nav-drawer__subitem"
          >
            <template v-slot:append>
              <v-badge
                v-if="getOpenTodosForWorld() > 0"
                :content="getOpenTodosForWorld()"
                color="warning"
                inline
              ></v-badge>
              <span class="nav-drawer__delete-spacer"></span>
            </template>
          </v-list-item>

          <!-- Encounters -->
          <v-list-item
            v-for="encounter in encountersList"
            :key="encounter"
            :to="`/game/${$route.params.gameName}/encounter/${encounter}`"
            prepend-icon="mdi-map-marker"
            :title="getEncounterDisplayName(encounter)"
            class="nav-drawer__subitem"
          >
            <template v-slot:append>
              <v-badge
                v-if="getOpenTodosForEncounter(encounter) > 0"
                :content="getOpenTodosForEncounter(encounter)"
                color="warning"
                inline
              ></v-badge>
              <RetroButton
                @click.stop="openDeleteDialog(encounter)"
                variant="reset"
                size="icon"
                class="nav-drawer__delete-btn"
                title="Delete encounter"
              >X</RetroButton>
            </template>
          </v-list-item>
        </template>

        <!-- Compact mode alternative -->
        <v-list-item
          v-else-if="isCompact && $route.params.gameName"
          :to="`/game/${$route.params.gameName}/world`"
          prepend-icon="mdi-state-machine"
          class="nav-drawer__item"
        >
        </v-list-item>
      </v-list>
    </v-navigation-drawer>

    <v-main class="content-area">
      <router-view :key="$route.fullPath"></router-view>
    </v-main>

    <!-- Delete Encounter Dialog -->
    <confirm-encounter-delete-dialog
      v-model="deleteDialogVisible"
      :encounter-id="deletingEncounterId"
      :encounter-name="deletingEncounterName"
      @confirm="handleEncounterDelete"
    />
  </v-app>
</template>

<script>
import ApplicationHeader from './components/ApplicationHeader.vue';
import ConfirmEncounterDeleteDialog from './components/ConfirmEncounterDeleteDialog.vue';
import RetroButton from './components/RetroButton.vue';
import { mapActions } from 'vuex';

export default {
  components: {
    ApplicationHeader,
    ConfirmEncounterDeleteDialog,
    RetroButton,
  },
  data() {
    return {
      navigationItems: [
        { title: 'Personality',    route: (gameName) => gameName ? `/game/${gameName}/personality` : '#', icon: 'mdi-account-alert-outline'},
        { title: 'Welcome Prompt', route: (gameName) => gameName ? `/game/${gameName}/welcome` : '#', icon: 'mdi-message-text-clock-outline'},
        { title: 'Inventory',      route: (gameName) => gameName ? `/game/${gameName}/inventory` : '#', icon: 'mdi-hand-coin-outline' },
        { title: 'Game Map',       route: (gameName) => gameName ? `/game/${gameName}/world` : '#', icon: 'mdi-state-machine'     },
      ],
      isCompact: false,
      deleteDialogVisible: false,
      deletingEncounterId: '',
      deletingEncounterName: '',
    };
  },
  computed: {
    drawerWidth() {
      // Laptop screens (< 1440px): narrower width (180px)
      // Larger screens (≥ 1440px): 300px
      if (this.$vuetify.display.width < 1440) {
        return 180;
      }
      return 300;
    },
    currentGameName() {
      return this.$store.getters['game/gameName'] || this.$route.params.gameName || null;
    },
    encountersList() {
      return this.$store.getters['encounters/encounterNames'] || [];
    },
  },
  created() {
    const storedState = localStorage.getItem('drawerCompactState');
    if (storedState !== null) {
      this.isCompact = JSON.parse(storedState);
    }

    window.addEventListener('beforeunload', this.handleBeforeUnload);

    // Initialize Stores
    this.initializeAll();
  },
  beforeUnmount() {
    window.removeEventListener('beforeunload', this.handleBeforeUnload);
  },
  methods: {
    ...mapActions('game', {
      initializeGame: 'initialize',
      loadGame: 'loadGame',
    }),
    ...mapActions('games', {
      initializeGames: 'initialize',
    }),
    ...mapActions('sounds', {
      initializeSounds: 'initialize',
    }),
    
    async initializeAll() {
      await Promise.all([
        this.initializeGame(),
        this.initializeGames(),
        this.initializeSounds()
      ]);
      
      if (this.$route.params.gameName) {
        await this.loadGame(this.$route.params.gameName);
      }
    },
    
    toggleDrawerCompact() {
      this.isCompact = !this.isCompact;
      localStorage.setItem('drawerCompactState', JSON.stringify(this.isCompact));
    },
    getEncounterDisplayName(encounterId) {
      const encounter = this.$store.state.encounters?.encounters?.[encounterId];
      return encounter?.name || encounterId;
    },
    getOpenTodosForEncounter(encounterId) {
      const viewId = `encounter_${encounterId}`;
      return this.$store.getters['views/openTodosForView'](viewId) || 0;
    },
    getOpenTodosForWorld() {
      return this.$store.getters['views/openTodosForView']('world') || 0;
    },
    openDeleteDialog(encounterId) {
      this.deletingEncounterId = encounterId;
      this.deletingEncounterName = this.getEncounterDisplayName(encounterId);
      this.deleteDialogVisible = true;
    },
    handleBeforeUnload(event) {
      const hasUnsavedChanges = this.$store.getters['game/hasUnsavedChanges'];
      if (hasUnsavedChanges) {
        event.preventDefault();
        event.returnValue = ''; 
        return ''; 
      }
    },
    openAddEncounterDialog() {
      const targetPath = `/game/${this.$route.params.gameName}/world`;
      if (this.$route.path === targetPath) {
        window.dispatchEvent(new CustomEvent('open-add-encounter-dialog'));
      } else {
        this.$router.push({
          path: targetPath,
          query: { addEncounter: 'true' }
        });
      }
    },
    async handleEncounterDelete(encounterId) {
      try {
        const viewId = `encounter_${encounterId}`;
        await this.$store.dispatch('views/deleteView', {
          gameName: this.$route.params.gameName,
          viewId
        });
        await this.$store.dispatch('encounters/fetchEncounters', this.$route.params.gameName);
        if (this.$route.params.encounterId === encounterId) {
          this.$router.replace(`/game/${this.$route.params.gameName}/world`);
        }
      } catch (error) {
        console.error('Failed to delete encounter:', error);
      }
    },
  },
};
</script>

<style>
/* Navigation Drawer */
.nav-drawer {
  background: var(--game-bg-secondary) !important;
  border-right: 3px solid var(--game-accent-primary) !important;
  border-radius: 0 !important;
}

.nav-drawer__toggle {
  min-height: 64px !important;
  cursor: pointer;
}

.nav-drawer__toggle .v-icon {
  color: var(--game-accent-secondary) !important;
  font-size: 28px !important;
  filter: drop-shadow(0 0 8px var(--game-accent-secondary)) !important;
  transition: all var(--game-transition-fast) !important;
}

.nav-drawer__game-name {
  padding: 8px 16px;
  margin: 0 8px 8px 8px;
  background: rgba(243, 156, 18, 0.1);
  border: 2px solid var(--game-accent-secondary);
}

.nav-drawer__game-label {
  font-family: var(--game-font-family-retro, 'Press Start 2P', monospace);
  font-size: 10px;
  color: var(--game-accent-secondary);
}

.nav-drawer__list {
  background: transparent !important;
  padding: var(--game-spacing-md) 0 !important;
}

.nav-drawer__item {
  margin: var(--game-spacing-xs) var(--game-spacing-sm) !important;
}

.nav-drawer__item.v-list-item--active {
  background: rgba(233, 69, 96, 0.15) !important;
  border-left: 3px solid var(--game-accent-secondary) !important;
  border-top: 2px solid var(--game-accent-secondary) !important;
  border-bottom: 2px solid var(--game-accent-primary) !important;
}

.nav-drawer__subitem {
  margin: 0 var(--game-spacing-sm) !important;
  padding-left: 40px !important;
  min-height: 32px !important;
}

.nav-drawer__subitem.v-list-item--active {
  background: rgba(233, 69, 96, 0.1) !important;
  border-left: 2px solid var(--game-accent-secondary) !important;
}

.nav-drawer__header {
  opacity: 0.7 !important;
  margin-top: var(--game-spacing-md) !important;
  border-top: 1px solid rgba(233, 69, 96, 0.2) !important;
}

.nav-drawer__header-title {
  font-weight: 600 !important;
  font-size: 0.75rem !important;
  text-transform: uppercase !important;
}

/* Specialized Overrides for Drawer Buttons */
.nav-drawer__add-btn {
  width: 20px;
  height: 20px;
}

.nav-drawer__delete-btn {
  width: 20px;
  height: 20px;
  opacity: 0;
}

.nav-drawer__subitem:hover .nav-drawer__delete-btn {
  opacity: 1;
}

.nav-drawer__delete-spacer {
  width: 20px;
  display: inline-block;
}
</style>

<style scoped>
.content-area {
  /* Use viewport relative height but respect the header height */
  /* header is 128px on large, 48px on small */
  --header-height: 128px;
  height: calc(100vh - var(--header-height));
  overflow: hidden;
}

@media (max-width: 959px) { /* Vuetify sm breakpoint */
  .content-area {
    --header-height: 48px;
  }
}

.content-area :deep(.v-main__wrap) {
  height: 100%;
  display: flex;
  flex-direction: column;
}
</style>

