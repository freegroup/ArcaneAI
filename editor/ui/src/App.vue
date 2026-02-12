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
      <v-list-item @click="toggleDrawerCompact" class="nav-drawer__toggle">
        <v-list-item-icon>
          <v-icon>{{ isCompact ? 'mdi-chevron-right' : 'mdi-chevron-left' }}</v-icon>
        </v-list-item-icon>
      </v-list-item>

      <v-divider></v-divider>

      <v-list dense class="nav-drawer__list">
        <v-list-item
          v-for="item in navigationItems"
          :key="item.title"
          :to="item.route($route.params.mapName)"
          :prepend-icon="item.icon"
          router
          class="nav-drawer__item"
        >
          <v-list-item-content v-if="!isCompact">
            <v-list-item-title>{{ item.title }}</v-list-item-title>
          </v-list-item-content>
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
        { title: 'Personality',  route: (mapName) => `/gamesetup/${mapName || ''}`, icon: 'mdi-account-alert-outline'},
        { title: 'Inventory',    route: (mapName) => `/inventory/${mapName || ''}`, icon: 'mdi-hand-coin-outline' },
        { title: 'Game Map', route: (mapName) => `/diagram/${mapName   || ''}`, icon: 'mdi-state-machine'     },
      ],
      isCompact: false,
      windowWidth: window.innerWidth,
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
  },
  created() {
    // Load the drawer state from localStorage
    const storedState = localStorage.getItem('drawerCompactState');
    if (storedState !== null) {
      this.isCompact = JSON.parse(storedState);
    }

    // Listen for window resize to update drawer width responsively
    window.addEventListener('resize', this.handleResize);

    // Initialize Map and Sounds
    setTimeout(async () => {
      this.initializeMap();
      this.initializeSounds();
      await this.downloadMap(this.$route.params.mapName || '');
    }, 500);
  },
  beforeUnmount() {
    // Clean up resize listener
    window.removeEventListener('resize', this.handleResize);
  },
  methods: {
    ...mapActions('maps', {
      initializeMap: 'initialize',
      downloadMap: 'downloadMap',
    }),
    ...mapActions('sounds', {
      initializeSounds: 'initialize',
    }),
    handleRequestDocument() {
      // Request Draw2d Document im aktuellen View
      const iframeComponent = this.$refs.iframeContainer;

      if (iframeComponent && iframeComponent.requestDraw2dDocument) {
        iframeComponent.requestDraw2dDocument();
        console.log('Request sent to iframe component');
      } else {
        console.error('Iframe component or requestDraw2dDocument method not found');
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

/* Responsive padding and spacer for laptop screens */
@media (max-width: 1439px) {
  .nav-drawer__item {
    padding-left: 5px !important;
  }
  
  .nav-drawer__item .v-list-item__spacer {
    width: 5px !important;
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
