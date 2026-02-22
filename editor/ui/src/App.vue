<template>
  <v-app id="app">
    <application-header />

    <!-- Navigation Drawer with Router Links -->
    <v-navigation-drawer
      app
      :permanent="true"
      :mini-variant="isCompact"
      :width="isCompact ? 56 : drawerWidth"
      :mini-variant-width="56"
      class="nav-drawer"
    >
      <!-- Toggle button to control compact state -->
      <v-list-item 
        @click="toggleDrawerCompact" 
        class="nav-drawer__toggle"
        :prepend-icon="isCompact ? 'mdi-chevron-right' : 'mdi-chevron-left'"
      >
      </v-list-item>

      <v-divider></v-divider>

      <v-list dense class="nav-drawer__list">
        <!-- Regular navigation items (not Game Map) -->
        <v-list-item
          v-for="item in navigationItems.filter(i => i.title !== 'Game Map')"
          :key="item.title"
          :to="item.route($route.params.gameName)"
          :prepend-icon="item.icon"
          :title="isCompact ? undefined : item.title"
          router
          class="nav-drawer__item"
        >
        </v-list-item>

        <!-- Game Map - Static Header (always visible) -->
        <template v-if="!isCompact && $route.params.gameName">
          <v-list-item
            prepend-icon="mdi-state-machine"
            class="nav-drawer__item nav-drawer__header nav-drawer__header--clickable"
          >
            <template v-slot:default>
              <span class="nav-drawer__header-title">Game Map</span>
            </template>
            <template v-slot:append>
              <button
                @click.prevent.stop="openAddEncounterDialog"
                class="nav-drawer__add-btn"
                title="Add new encounter"
              >+</button>
            </template>
          </v-list-item>

          <!-- World - Main Game (always called "World") -->
          <v-list-item
            :to="`/game/${$route.params.gameName}/world`"
            prepend-icon="mdi-earth"
            title="World"
            class="nav-drawer__subitem"
            router
          >
            <template v-slot:append>
              <v-badge
                v-if="getOpenTodosForWorld() > 0"
                :content="getOpenTodosForWorld()"
                color="warning"
                class="encounter-todo-badge"
                inline
              ></v-badge>
              <!-- Ghost spacer to align with delete button on encounters -->
              <span class="nav-drawer__delete-spacer"></span>
            </template>
          </v-list-item>

          <!-- Encounters - Direct children, no subfolder -->
          <v-list-item
            v-for="encounter in encountersList"
            :key="encounter"
            :to="`/game/${$route.params.gameName}/encounter/${encounter}`"
            prepend-icon="mdi-map-marker"
            :title="getEncounterDisplayName(encounter)"
            class="nav-drawer__subitem"
            router
          >
            <template v-slot:append>
              <v-badge
                v-if="getOpenTodosForEncounter(encounter) > 0"
                :content="getOpenTodosForEncounter(encounter)"
                color="warning"
                class="encounter-todo-badge"
                inline
              ></v-badge>
              <button
                @click.prevent.stop="openDeleteDialog(encounter)"
                class="nav-drawer__delete-btn"
                title="Delete encounter"
              >X</button>
            </template>
          </v-list-item>
        </template>

        <!-- Compact mode: Just show Game Map as single item -->
        <v-list-item
          v-else-if="isCompact && $route.params.gameName"
          :to="`/game/${$route.params.gameName}/world`"
          prepend-icon="mdi-state-machine"
          router
          class="nav-drawer__item"
        >
        </v-list-item>
      </v-list>
    </v-navigation-drawer>

    <v-main class="content-area">
      <router-view ref="iframeContainer"></router-view>
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
import { mapActions } from 'vuex';

export default {
  components: {
    ApplicationHeader,
    ConfirmEncounterDeleteDialog,
  },
  data() {
    return {
      navigationItems: [
        { title: 'Personality',  route: (gameName) => gameName ? `/game/${gameName}/personality` : '#', icon: 'mdi-account-alert-outline'},
        { title: 'Inventory',    route: (gameName) => gameName ? `/game/${gameName}/inventory` : '#', icon: 'mdi-hand-coin-outline' },
        { title: 'Game Map', route: (gameName) => gameName ? `/game/${gameName}/world` : '#', icon: 'mdi-state-machine'     },
      ],
      isCompact: false,
      windowWidth: window.innerWidth,
      openedGroups: ['game-map'],
      // Delete Encounter Dialog state
      deleteDialogVisible: false,
      deletingEncounterId: '',
      deletingEncounterName: '',
      // Add Encounter Dialog state
      addEncounterDialogVisible: false,
    };
  },
  computed: {
    drawerWidth() {
      // Laptop screens (< 1440px): narrower width (180px)
      // Larger screens (≥ 1440px): 1/4 wider (300px instead of 240px)
      if (this.windowWidth < 1440) {
        return 180;
      }
      return 300;
    },
    encountersList() {
      return this.$store.getters['encounters/encounterNames'] || [];
    },
    totalOpenTodos() {
      return this.$store.getters['views/totalOpenTodos'] || 0;
    },
  },
  created() {
    // Load the drawer state from localStorage
    const storedState = localStorage.getItem('drawerCompactState');
    if (storedState !== null) {
      this.isCompact = JSON.parse(storedState);
    }

    // Listen for window resize to update drawer width responsively
    window.addEventListener('resize', this.handleResize);
    
    // Warn user about unsaved changes on page reload/close
    window.addEventListener('beforeunload', this.handleBeforeUnload);

    // Initialize Stores and Sounds
    setTimeout(async () => {
      this.initializeGame();
      this.initializeGames();
      this.initializeSounds();
      // Load game if gameName is in route
      if (this.$route.params.gameName) {
        await this.loadGame(this.$route.params.gameName);
      }
    }, 500);
  },
  beforeUnmount() {
    // Clean up resize listener
    window.removeEventListener('resize', this.handleResize);
    // Clean up beforeunload listener
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
    toggleDrawerCompact() {
      this.isCompact = !this.isCompact;
      localStorage.setItem('drawerCompactState', JSON.stringify(this.isCompact));
    },
    handleResize() {
      this.windowWidth = window.innerWidth;
    },
    getEncounterDisplayName(encounterId) {
      // Get display name from encounterConfig or fallback to encounterId
      const encounter = this.$store.state.encounters?.encounters?.[encounterId];
      return encounter?.name || encounterId;
    },
    getOpenTodosForEncounter(encounterId) {
      // Get open todos count for a specific encounter view
      const viewId = `encounter_${encounterId}`;
      return this.$store.getters['views/openTodosForView'](viewId) || 0;
    },
    getOpenTodosForWorld() {
      // Get open todos count for the world view
      return this.$store.getters['views/openTodosForView']('world') || 0;
    },
    openDeleteDialog(encounterId) {
      this.deletingEncounterId = encounterId;
      this.deletingEncounterName = this.getEncounterDisplayName(encounterId);
      this.deleteDialogVisible = true;
    },
    handleBeforeUnload(event) {
      // Check if there are unsaved changes in the model store
      const hasUnsavedChanges = this.$store.getters['model/hasUnsavedChanges'];
      if (hasUnsavedChanges) {
        // Standard way to show browser's "unsaved changes" dialog
        event.preventDefault();
        event.returnValue = ''; // Required for Chrome
        return ''; // Required for some browsers
      }
    },
    openAddEncounterDialog() {
      // Navigate to world view with addEncounter query param to trigger dialog
      this.$router.push({
        path: `/game/${this.$route.params.gameName}/world`,
        query: { addEncounter: 'true' }
      });
    },
    async handleEncounterDelete(encounterId) {
      try {
        const viewId = `encounter_${encounterId}`;
        
        // Delete the view from server and store
        await this.$store.dispatch('views/deleteView', {
          gameName: this.$route.params.gameName,
          viewId
        });
        
        // Reload encounters to refresh navigation
        await this.$store.dispatch('encounters/fetchEncounters', this.$route.params.gameName);
        
        // Navigate to world if we're currently viewing the deleted encounter
        if (this.$route.params.encounterId === encounterId) {
          this.$router.replace(`/game/${this.$route.params.gameName}/world`);
        }
        
        console.log(`Encounter ${encounterId} deleted successfully`);
      } catch (error) {
        console.error('Failed to delete encounter:', error);
      }
    },
  },
};
</script>

<style>
/* Navigation Drawer - Einfaches 8-Bit Styling */
.nav-drawer {
  background: var(--game-bg-secondary) !important;
  border-right: 3px solid var(--game-accent-primary) !important;
  border-radius: 0 !important;
}

/* Toggle Button */
.nav-drawer__toggle {
  background: transparent !important;
  min-height: 64px !important;
}

.nav-drawer__toggle .v-icon {
  color: var(--game-accent-secondary) !important;
  font-size: 28px !important;
  filter: drop-shadow(0 0 8px var(--game-accent-secondary)) !important;
  transition: all var(--game-transition-fast) !important;
}

.nav-drawer__toggle:hover .v-icon {
  filter: drop-shadow(0 0 12px var(--game-accent-secondary)) !important;
  transform: scale(1.1) !important;
}

/* Divider verstecken */
.nav-drawer .v-divider {
  display: none !important;
}

/* List Items */
.nav-drawer__list {
  background: transparent !important;
  padding: var(--game-spacing-md) 0 !important;
}

.nav-drawer__item {
  border-radius: 0 !important;
  margin: var(--game-spacing-xs) var(--game-spacing-sm) !important;
}

/* Responsive padding and spacer for medium screens (Laptops) */
@media (max-width: 1439px) {
  .nav-drawer__item {
    padding-left: var(--screen-medium-drawer-item-padding, 5px) !important;
  }
  
  .nav-drawer__item .v-list-item__spacer {
    width: var(--screen-medium-drawer-spacer, 5px) !important;
  }
}

/* Responsive padding and spacer for small screens */
@media (max-width: 1023px) {
  .nav-drawer__item {
    padding-left: var(--screen-small-drawer-item-padding, 4px) !important;
  }
  
  .nav-drawer__item .v-list-item__spacer {
    width: var(--screen-small-drawer-spacer, 4px) !important;
  }
}

/* Active Item - NUR dieser bekommt Styling */
.nav-drawer__item.v-list-item--active {
  background: rgba(233, 69, 96, 0.15) !important;
  border-left: 3px solid var(--game-accent-secondary) !important;
  border-top: 2px solid var(--game-accent-secondary) !important;
  border-bottom: 2px solid var(--game-accent-primary) !important;
}

.nav-drawer__item.v-list-item--active .v-icon {
  color: var(--game-accent-secondary) !important;
}

.nav-drawer__item.v-list-item--active .v-list-item-title {
  color: var(--game-accent-secondary) !important;
  font-weight: 600 !important;
}

/* Subitem Styling (World + Encounters) */
.nav-drawer__subitem {
  border-radius: 0 !important;
  margin: 0 var(--game-spacing-sm) !important;
  padding-left: 40px !important;
  min-height: 32px !important;
  font-size: 0.875rem !important;
}

.nav-drawer__subitem .v-list-item__prepend {
  width: 28px !important;
  min-width: 28px !important;
}

.nav-drawer__subitem .v-icon {
  font-size: 18px !important;
  opacity: 0.8 !important;
}

.nav-drawer__subitem .v-list-item-title {
  font-size: 0.875rem !important;
}

/* Active Subitem */
.nav-drawer__subitem.v-list-item--active {
  background: rgba(233, 69, 96, 0.1) !important;
  border-left: 2px solid var(--game-accent-secondary) !important;
  border-top: 1px solid var(--game-accent-secondary) !important;
  border-bottom: 1px solid var(--game-accent-primary) !important;
}

.nav-drawer__subitem.v-list-item--active .v-icon {
  color: var(--game-accent-secondary) !important;
  opacity: 1 !important;
}

.nav-drawer__subitem.v-list-item--active .v-list-item-title {
  color: var(--game-accent-secondary) !important;
  font-weight: 500 !important;
}

/* Header Styling (Game Map Label) */
.nav-drawer__header {
  opacity: 0.7 !important;
  cursor: default !important;
  margin-top: var(--game-spacing-md) !important;
  border-top: 1px solid rgba(233, 69, 96, 0.2) !important;
  padding-top: var(--game-spacing-sm) !important;
}

/* Header with add button - clickable */
.nav-drawer__header--clickable {
  pointer-events: auto !important;
}

.nav-drawer__header-title {
  font-weight: 600 !important;
  font-size: 0.75rem !important;
  text-transform: uppercase !important;
  letter-spacing: 0.5px !important;
}

/* Add Button - 8-Bit Style (Green) */
.nav-drawer__add-btn {
  background: var(--game-success, #28a745);
  color: white;
  border: none;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-family: var(--game-font-family-retro, 'Press Start 2P', monospace);
  font-size: 10px;
  font-weight: bold;
  position: relative;
  box-shadow: inset -2px -2px 0px 0px #1e7e34;
  transition: all 0.15s ease;
  pointer-events: auto;
}

.nav-drawer__add-btn::before {
  content: '';
  position: absolute;
  top: -2px;
  left: 0;
  width: 100%;
  height: 100%;
  border-top: 2px solid black;
  border-bottom: 2px solid black;
  box-sizing: content-box;
  pointer-events: none;
}

.nav-drawer__add-btn::after {
  content: '';
  position: absolute;
  left: -2px;
  top: 0;
  width: 100%;
  height: 100%;
  border-left: 2px solid black;
  border-right: 2px solid black;
  box-sizing: content-box;
  pointer-events: none;
}

.nav-drawer__add-btn:hover {
  background: #229954;
  box-shadow: inset -3px -3px 0px 0px #1e7e34;
}

.nav-drawer__add-btn:active {
  box-shadow: inset 2px 2px 0px 0px #1e7e34;
}

.nav-drawer__header .v-icon {
  opacity: 0.6 !important;
}

.nav-drawer__header .v-list-item-title {
  font-weight: 600 !important;
  font-size: 0.75rem !important;
  text-transform: uppercase !important;
  letter-spacing: 0.5px !important;
}

/* Delete Button Styling - 8-Bit Button (like dialog close) */
.nav-drawer__delete-btn {
  opacity: 0;
  transition: all 0.2s ease;
  background: var(--game-accent-primary);
  color: white;
  border: none;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-family: var(--game-font-family-retro, 'Press Start 2P', monospace);
  font-size: 8px;
  font-weight: bold;
  position: relative;
  box-shadow: inset -2px -2px 0px 0px #8c2022;
}

.nav-drawer__delete-btn::before {
  content: '';
  position: absolute;
  top: -2px;
  left: 0;
  width: 100%;
  height: 100%;
  border-top: 2px solid black;
  border-bottom: 2px solid black;
  box-sizing: content-box;
  pointer-events: none;
}

.nav-drawer__delete-btn::after {
  content: '';
  position: absolute;
  left: -2px;
  top: 0;
  width: 100%;
  height: 100%;
  border-left: 2px solid black;
  border-right: 2px solid black;
  box-sizing: content-box;
  pointer-events: none;
}

.nav-drawer__subitem:hover .nav-drawer__delete-btn {
  opacity: 0.8;
}

.nav-drawer__delete-btn:hover {
  opacity: 1 !important;
  background: #ce372b;
  box-shadow: inset -3px -3px 0px 0px #8c2022;
}

.nav-drawer__delete-btn:active {
  box-shadow: inset 2px 2px 0px 0px #8c2022;
}

/* Ghost spacer for World item (same size as delete button for alignment) */
.nav-drawer__delete-spacer {
  width: 20px;
  height: 20px;
  display: inline-block;
}
</style>

<style scoped>
#app {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}

.content-area {
  overflow: hidden;
}
</style>

