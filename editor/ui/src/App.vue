<template>
  <v-app id="app">
    <app-toolbar density="compact" dark @requestDocument="handleRequestDocument" />

    <!-- Navigation Drawer with Router Links -->
    <v-navigation-drawer
      app
      :permanent="true"
      :mini-variant="isCompact"
      :width="isCompact ? 56 : 240"
      :mini-variant-width="56"
    >
      <!-- Toggle button to control compact state -->
      <v-list-item @click="toggleDrawerCompact" style="cursor: pointer;">
        <v-list-item-icon>
          <v-icon>{{ isCompact ? 'mdi-chevron-right' : 'mdi-chevron-left' }}</v-icon>
        </v-list-item-icon>
      </v-list-item>

      <v-divider></v-divider>

      <v-list dense>
        <v-list-item
          v-for="item in navigationItems"
          :key="item.title"
          :to="item.route($route.params.mapName)"
          :prepend-icon="item.icon"
          router
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
        { title: 'Personality',  route: (mapName) => `/gamesetup/${mapName || ''}`, icon: 'mdi-axis-arrow-info'   },
        { title: 'Inventory',    route: (mapName) => `/inventory/${mapName || ''}`, icon: 'mdi-hand-coin-outline' },
        { title: 'State Engine', route: (mapName) => `/diagram/${mapName   || ''}`, icon: 'mdi-state-machine'     },
      ],
      isCompact: false, // Initially, the drawer is expanded
    };
  },
  created() {
    // Load the drawer state from localStorage
    const storedState = localStorage.getItem('drawerCompactState');
    if (storedState !== null) {
      this.isCompact = JSON.parse(storedState);
    }

    // Initialize Map and Sounds
    setTimeout(async () => {
      this.initializeMap();
      this.initializeSounds();
      await this.downloadMap(this.$route.params.mapName || '');
    }, 500);
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
      // Toggle compact state and save to localStorage
      this.isCompact = !this.isCompact;
      localStorage.setItem('drawerCompactState', JSON.stringify(this.isCompact));
    },
  },
};
</script>

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
  justify-content: start;
  align-items: center;
}
</style>
