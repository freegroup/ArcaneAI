  <template>
    <v-app id="app">

        <app-toolbar @requestDocument="handleRequestDocument" />

        <!-- Navigation Drawer with Router Links -->
        <v-navigation-drawer app permanent  width="240">
          <v-list dense>
            <v-list-item
              v-for="item in navigationItems"
              :key="item.title"
              :to="item.route"
              :prepend-icon="item.icon"
              router>

              <v-list-item-content>
                <v-list-item-title>{{ item.title }}</v-list-item-title>
              </v-list-item-content>
            </v-list-item>
          </v-list>
        </v-navigation-drawer>
        
        <v-main class="content-area">
          <router-view  ref="iframeContainer"></router-view>
        </v-main>

    </v-app>
  </template>


  <script>
  import AppToolbar from './components/AppToolbar.vue'; 
  import { mapActions } from 'vuex';

  export default {
    components: {
      AppToolbar
    },
    data() {
      return {
        navigationItems: [
          { title: 'Sceen Setup',  route: '/configuration' , icon: 'mdi-cog'},
          { title: 'Inventory',    route: '/inventory'     , icon: 'mdi-hand-coin-outline'},
          { title: 'State Engine', route: '/diagram'       , icon:'mdi-state-machine' },
        ],
      };
    },
    created() {
      // Call the namespaced initialize action from the map module
      setTimeout(async () => {
        this.initializeMap();
        this.initializeSounds()
        await this.downloadMap(this.$route.params.mapName || '');
      }, 500);
    },
  
    methods: {
      ...mapActions('maps', {
        initializeMap: 'initialize',
        downloadMap: "downloadMap"
      }),
      ...mapActions('sounds', {
        initializeSounds: 'initialize'
      }),
      handleRequestDocument() {
        // Call the requestDraw2dDocument method in the Iframe component
      // Check if the router-view has a component and that component has the method
      const iframeComponent = this.$refs.iframeContainer;

      if (iframeComponent && iframeComponent.requestDraw2dDocument) {
        iframeComponent.requestDraw2dDocument(); // Call the method directly on the component
        console.log("Request sent to iframe component");
      } else {
        console.error("Iframe component or requestDraw2dDocument method not found");
      }
        console.log("Request")
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
    background-color: #f0f0f0;
  }
  </style>
