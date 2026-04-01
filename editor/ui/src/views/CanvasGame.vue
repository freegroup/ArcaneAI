<template>
  <div class="canvas-game-container">
    <!-- Canvas iframe takes main area -->
    <div class="iframe-container">
      <iframe
        ref="draw2dFrame"
        src="/canvas/world/index.html"
        frameborder="0"
      ></iframe>
    </div>

    <!-- Property Sidebar using Vuetify Navigation Drawer -->
    <v-navigation-drawer
      location="right"
      permanent
      :width="sidebarCollapsed ? 0 : sidebarWidth"
      class="property-drawer"
    >
    <!-- Toggle Button - outside drawer, always visible -->
    <button class="sidebar-toggle" @click="toggleSidebar" :title="sidebarCollapsed ? 'Expand panel' : 'Collapse panel'">
        {{ sidebarCollapsed ? '◀' : '▶' }}
    </button>
      <!-- Property content -->
      <div class="property-drawer__content" v-show="!sidebarCollapsed">
        <EncounterPropertyView v-if="draw2dFrameContent" :draw2dFrame="draw2dFrameContent"/>
        <StateProperty v-if="draw2dFrameContent" :draw2dFrame="draw2dFrameContent"/>
        <StateTriggerProperty v-if="draw2dFrameContent" :draw2dFrame="draw2dFrameContent"/>
        <ConnectionTriggerProperty v-if="draw2dFrameContent" :draw2dFrame="draw2dFrameContent"/>
      </div>
    </v-navigation-drawer>


    <!-- Chat Dialog -->
    <ChatDialog 
      v-model="showChatDialog" 
      :stateName="chatDialogStateName"
    />

    <!-- Create View Dialog -->
    <EncounterNewDialog
      v-model="showCreateViewDialog"
      :initialName="createViewDefaultName"
      @created="onEncounterCreated"
    />
  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex';
import StateProperty from './StateProperty.vue';
import StateTriggerProperty from './StateTriggerProperty.vue';
import ConnectionTriggerProperty from './ConnectionTriggerProperty.vue';
import EncounterPropertyView from './EncounterPropertyView.vue';
import ChatDialog from '../components/ChatDialog.vue';

import EncounterNewDialog from '../components/EncounterNewDialog.vue';
import { MessageTypes } from '../../public/shared/SharedConstants.js';
import ViewComposer from '../utils/ViewComposer.js';

export default {
  components: {
    StateProperty,
    StateTriggerProperty,
    ConnectionTriggerProperty,
    EncounterPropertyView,
    ChatDialog,
   
    EncounterNewDialog
  },
  data() {
    return {
      draw2dFrameContent: null,
      canvasReady: false,
      isCanvasUpdate: false,
      showChatDialog: false,
      chatDialogStateName: '',
      sidebarCollapsed: false,
      showCreateViewDialog: false,
      createViewDefaultName: '',
      pendingViewData: null
    };
  },
  computed: {
    ...mapGetters('game', ['gameName']),
    ...mapGetters('model', ['allStates', 'allConnections']),
    ...mapGetters('views', ['currentView']),
    ...mapGetters('settings', ['currentTheme']),
    
    composedDiagram() {
      const model = {
        states: this.$store.state.model.states,
        connections: this.$store.state.model.connections
      };
      const view = this.currentView;
      return ViewComposer.compose(model, view);
    },
    
    mapName() {
      return this.gameName;
    },
    draw2dFrame() {
      return this.$refs.draw2dFrame;
    },
    sidebarWidth() {
      /**
       * Use Vuetify's built-in display system.
       * Laptop screens (< 1440px): 350px
       * Larger screens (≥ 1440px): 600px
       */
      return this.$vuetify.display.width >= 1440 ? 600 : 350;
    }
  },
  watch: {
    composedDiagram: {
      handler(newDiagram) {
        if (newDiagram && this.canvasReady) {
          if (this.isCanvasUpdate) return;
          if (this.$store.state.model.isPropertyUpdate) return;
          this.sendDocumentToCanvas(newDiagram);
        }
      },
      deep: true,
      immediate: false,
    },
    currentTheme(theme) {
      this.sendThemeToCanvas(theme);
    },
  },
  methods: {
    ...mapActions('model', ['setModel', 'mergeModel', 'removeState', 'removeConnection', 'saveModel']),
    ...mapActions('views', ['updateCurrentViewLayout', 'saveView', 'setCurrentView', 'createEncounterView']),
    
    toggleSidebar() {
      this.sidebarCollapsed = !this.sidebarCollapsed;
      localStorage.setItem('sidebarCollapsed', JSON.stringify(this.sidebarCollapsed));
    },
    
    async saveMap() {
      try {
        await this.saveModel();
        await this.saveView({ viewId: 'world' });
      } catch (error) {
        console.error('[CanvasGame] Save failed:', error);
        throw error;
      }
    },
    
    handleCanvasUpdate(diagram) {
      this.isCanvasUpdate = true;
      
      const newModel = ViewComposer.extractModel(diagram);
      const newLayout = ViewComposer.extractLayout(diagram);
      
      const currentView = this.currentView;
      const previousLayoutIds = Object.keys(currentView?.stateLayouts || {});
      const currentCanvasStateIds = Object.keys(newModel.states);
      const previousRouteIds = Object.keys(currentView?.connectionRoutes || {});
      const currentCanvasConnIds = Object.keys(newModel.connections);
      
      for (const stateId of previousLayoutIds) {
        if (!currentCanvasStateIds.includes(stateId)) {
          if (this.$store.state.model.states[stateId]) {
            this.removeState(stateId);
          }
        }
      }
      
      for (const connId of previousRouteIds) {
        if (!currentCanvasConnIds.includes(connId)) {
          if (this.$store.state.model.connections[connId]) {
            this.removeConnection(connId);
          }
        }
      }
      
      this.mergeModel(newModel);
      this.updateCurrentViewLayout(newLayout);
      
      this.$nextTick(() => {
        this.isCanvasUpdate = false;
      });
    },

    async saveReceivedDocument() {
      await this.saveMap();
    },
    
    updateDraw2dFrame() {
      if (this.$refs.draw2dFrame) {
        this.draw2dFrameContent = this.$refs.draw2dFrame.contentWindow;
      }
    },
    
    sendDocumentToCanvas(document) {
      window.postMessage({
        type: MessageTypes.V2C_SET_DOCUMENT,
        data: JSON.parse(JSON.stringify(document)),
        source: 'vue:world'
      }, '*');
    },

    sendThemeToCanvas(theme) {
      if (this.draw2dFrameContent) {
        this.draw2dFrameContent.postMessage({
          type: MessageTypes.V2C_SET_THEME,
          theme: theme
        }, '*');
      }
    },
    
    /**
     * Called when EncounterNewDialog creates a new encounter.
     * If we have pending viewData from "View from Here...", we add the layouts.
     * 
     * @param {string} viewId - The created view ID (e.g., 'encounter_tavern')
     */
    async onEncounterCreated(viewId) {
      if (this.pendingViewData) {
        // Extract layouts and routes from the pending viewData
        const stateLayouts = {};
        const connectionRoutes = {};
        
        for (const item of this.pendingViewData) {
          if (item.type === 'TriggerConnection') {
            connectionRoutes[item.id] = {
              vertex: item.vertex || [],
              routingMetaData: item.routingMetaData
            };
          } else if (item.name !== undefined && item.trigger !== undefined) {
            stateLayouts[item.id] = {
              x: item.x,
              y: item.y
            };
          }
        }
        
        // Update the view with layouts
        this.$store.commit('views/PATCH_VIEW', {
          viewId,
          patch: { stateLayouts, connectionRoutes }
        });
        
        // Save the view
        await this.saveView({ viewId });
        
        console.log(`[CanvasGame] Added ${Object.keys(stateLayouts).length} states to view ${viewId}`);
        
        // Clear pending data
        this.pendingViewData = null;
      }
    },

    /**
     * Creates a new encounter view from the selected state and its connections.
     * Called when user selects "View from Here..." in context menu.
     * 
     * @param {string} viewName - Name for the new view (from modal input)
     * @param {Array} viewData - Serialized diagram data (states + connections with positions)
     */
    async createViewFromState(viewName, viewData) {
      try {
        // 1. Create the encounter view
        const viewId = await this.createEncounterView({ encounterName: viewName });
        
        // 2. Extract layouts and routes from the viewData
        const stateLayouts = {};
        const connectionRoutes = {};
        
        for (const item of viewData) {
          if (item.type === 'TriggerConnection') {
            // Connection: extract routing info
            connectionRoutes[item.id] = {
              vertex: item.vertex || [],
              routingMetaData: item.routingMetaData
            };
          } else if (item.name !== undefined && item.trigger !== undefined) {
            // State: has 'name' and 'trigger' properties (from StateShape.getPersistentAttributes)
            stateLayouts[item.id] = {
              x: item.x,
              y: item.y
            };
          }
        }
        
        // 3. Update the view with layouts (using PATCH_VIEW)
        this.$store.commit('views/PATCH_VIEW', {
          viewId,
          patch: { stateLayouts, connectionRoutes }
        });
        
        // 4. Save the view to server
        await this.saveView({ viewId });
        
        // 5. Navigate to the new encounter view
        // Route param is 'encounterName' (slug without prefix), viewId is 'encounter_slug'
        const routeParam = viewId.replace(/^encounter_/, '');
        this.$router.push({ name: 'encounter', params: { encounterName: routeParam } });
        
        console.log(`[CanvasGame] Created encounter view "${viewName}" (${viewId}) with ${Object.keys(stateLayouts).length} states and ${Object.keys(connectionRoutes).length} connections`);
      } catch (error) {
        console.error('[CanvasGame] Failed to create view from state:', error);
      }
    },
  },
  mounted() {
    // Restore sidebar state from localStorage
    const storedState = localStorage.getItem('sidebarCollapsed');
    if (storedState !== null) {
      this.sidebarCollapsed = JSON.parse(storedState);
    }
    
    this.setCurrentView('world');
    
    this.$nextTick(() => {
      this.updateDraw2dFrame();
    });

    this.messageHandler = (event) => {
      if (event.origin !== window.location.origin) return;
      const message = event.data;
      
      switch (message.type) {
        case MessageTypes.C2V_CANVAS_READY:
          this.updateDraw2dFrame();
          this.canvasReady = true;
          this.sendThemeToCanvas(this.currentTheme);
          if (this.composedDiagram && this.composedDiagram.length > 0) {
            this.sendDocumentToCanvas(this.composedDiagram);
          }
          break;

        case MessageTypes.C2V_DOCUMENT_UPDATED:
          this.handleCanvasUpdate(message.data);
          break;

        case MessageTypes.C2V_CHAT_FROM_HERE:
          this.chatDialogStateName = message.stateName;
          this.showChatDialog = true;
          break;

        case MessageTypes.C2V_CREATE_VIEW_FROM_STATE:
          // Store viewData and show dialog with default name
          this.pendingViewData = message.viewData;
          this.createViewDefaultName = message.defaultName || '';
          this.showCreateViewDialog = true;
          break;

        default:
          if (message.type?.startsWith('v2c:') && this.draw2dFrameContent) {
            this.draw2dFrameContent.postMessage(message, '*');
          }
          break;
      }
    };
    window.addEventListener('message', this.messageHandler);
  },
  beforeUnmount() {
    if (this.messageHandler) {
      window.removeEventListener('message', this.messageHandler);
    }
  }
};
</script>

<style scoped>
.canvas-game-container {
  display: flex;
  overflow: hidden;
}

.iframe-container {
  flex: 1;
  display: flex;
}

.iframe-container iframe {
  flex: 1;
  border: none;
}

/* Toggle Button - fixed position, always visible */
.sidebar-toggle {
  position: absolute;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}
</style>

<style>
/* Content area */
.property-drawer__content {
  overflow-y: auto;
}
</style>
