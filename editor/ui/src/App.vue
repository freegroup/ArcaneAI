<template>
  <v-app id="app">
    <app-toolbar density="compact" dark @requestDocument="handleRequestDocument" />

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
            title="Game Map"
            class="nav-drawer__item nav-drawer__header"
            disabled
          >
          </v-list-item>

          <!-- World - Main Game (always called "World") -->
          <v-list-item
            :to="`/game/${$route.params.gameName}/world`"
            prepend-icon="mdi-earth"
            title="World"
            class="nav-drawer__subitem"
            router
          >
          </v-list-item>

          <!-- Encounters - Direct children, no subfolder -->
          <v-list-item
            v-for="encounter in encountersList"
            :key="encounter"
            :to="`/game/${$route.params.gameName}/encounter/${encounter}`"
            prepend-icon="mdi-map-marker"
            :title="encounter"
            class="nav-drawer__subitem"
            router
          >
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
  </v-app>
</template>

<script>
import AppToolbar from './components/AppToolbar.vue';
import { mapActions } from 'vuex';

export default {
  components: {
    AppToolbar,
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
    };
  },
  computed: {
    drawerWidth() {
      // Laptop screens (< 1440px): 25% narrower (180px instead of 240px)
      // Larger screens: full width (240px)
      if (this.windowWidth < 1440) {
        return 180;
      }
      return 240;
    },
    encountersList() {
      return this.$store.getters['encounters/encounterNames'] || [];
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
    handleRequestDocument() {
      // Request Draw2d Document im aktuellen View
      const iframeComponent = this.$refs.iframeContainer;

      if (iframeComponent && iframeComponent.requestDraw2dDocument) {
        iframeComponent.requestDraw2dDocument();
      }
    },
    toggleDrawerCompact() {
      this.isCompact = !this.isCompact;
      localStorage.setItem('drawerCompactState', JSON.stringify(this.isCompact));
    },
    handleResize() {
      this.windowWidth = window.innerWidth;
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
  margin: 2px var(--game-spacing-sm) !important;
  padding-left: 40px !important;
  min-height: 36px !important;
  font-size: 0.875rem !important;
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
  pointer-events: none !important;
  margin-top: var(--game-spacing-md) !important;
  border-top: 1px solid rgba(233, 69, 96, 0.2) !important;
  padding-top: var(--game-spacing-sm) !important;
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
</style>

<style scoped>
#app {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.content-area {
  overflow: hidden;
  flex: 1;
  display: flex;
  flex-direction: column;
}
</style>
