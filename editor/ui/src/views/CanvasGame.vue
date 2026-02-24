<template>
  <div class="canvas-game-container">
    <!-- Canvas iframe takes main area -->
    <div class="iframe-container">
      <iframe
        ref="draw2dFrame"
        src="/game/index.html"
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
      <!-- Property content -->
      <div class="property-drawer__content" v-show="!sidebarCollapsed">
        <EncounterPropertyView v-if="draw2dFrameContent" :draw2dFrame="draw2dFrameContent"/>
        <StateProperty v-if="draw2dFrameContent" :draw2dFrame="draw2dFrameContent"/>
        <StateTriggerProperty v-if="draw2dFrameContent" :draw2dFrame="draw2dFrameContent"/>
        <ConnectionTriggerProperty v-if="draw2dFrameContent" :draw2dFrame="draw2dFrameContent"/>
      </div>
    </v-navigation-drawer>

    <!-- Toggle Button - outside drawer, always visible -->
    <RetroButton 
      class="sidebar-toggle" 
      size="icon"
      @click="toggleSidebar" 
      :title="sidebarCollapsed ? 'Expand panel' : 'Collapse panel'"
    >
      {{ sidebarCollapsed ? '◀' : '▶' }}
    </RetroButton>
  
    <!-- Chat Dialog -->
    <ChatDialog 
      v-model="showChatDialog" 
      :stateName="chatDialogStateName"
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
import RetroButton from '../components/RetroButton.vue';
import { MessageTypes } from '../../public/shared/SharedConstants.js';
import ViewComposer from '../utils/ViewComposer.js';

export default {
  components: {
    StateProperty,
    StateTriggerProperty,
    ConnectionTriggerProperty,
    EncounterPropertyView,
    ChatDialog,
    RetroButton
  },
  data() {
    return {
      draw2dFrameContent: null,
      canvasReady: false,
      isCanvasUpdate: false,
      showChatDialog: false,
      chatDialogStateName: '',
      sidebarCollapsed: false
    };
  },
  computed: {
    ...mapGetters('game', ['gameName']),
    ...mapGetters('model', ['allStates', 'allConnections']),
    ...mapGetters('views', ['currentView']),
    
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
  },
  methods: {
    ...mapActions('model', ['setModel', 'mergeModel', 'removeState', 'removeConnection', 'saveModel']),
    ...mapActions('views', ['updateCurrentViewLayout', 'saveView', 'setCurrentView']),
    
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
  width: 100%;
  height: 100%;
  display: flex;
  overflow: hidden;
}

.iframe-container {
  flex: 1;
  min-width: 0;
  min-height: 0;
  display: flex;
}

.iframe-container iframe {
  flex: 1;
  width: 100%;
  height: 100%;
  border: none;
}
</style>

<style scoped>
/* Toggle Button - fixed position, always visible */
.sidebar-toggle {
  position: fixed;
  right: v-bind('sidebarCollapsed ? "0px" : sidebarWidth + "px"');
  top: 50%;
  transform: translateY(-50%);
  width: 32px;
  height: 48px;
  z-index: 1001;
  transition: right 0.3s ease;
  padding: 0;
}

/* We override the retro-btn defaults for the specialized toggle */
.sidebar-toggle :deep(.retro-btn) {
  border-radius: 4px 0 0 4px;
  border-right: none;
}
</style>

<style>
/* Property Drawer - matching left navigation */
.property-drawer {
  background: var(--game-bg-secondary) !important;
  border-left: 3px solid var(--game-accent-primary) !important;
  border-radius: 0 !important;
}

/* Content area */
.property-drawer__content {
  padding: var(--game-spacing-sm);
  overflow-y: auto;
  height: 100%;
}
</style>

<style scoped>
/* Container muss sich an den verfügbaren Platz anpassen, nicht an den Inhalt */
.canvas-game-container {
  width: 100%;
  height: 100%;
  display: flex;
  overflow: hidden;
}

.iframe-container {
  flex: 1;
  min-width: 0;
  min-height: 0;
  display: flex;
}

.iframe-container iframe {
  flex: 1;
  width: 100%;
  height: 100%;
  border: none;
}
</style>

<style scoped>
/* Toggle Button - fixed position, always visible */
.sidebar-toggle {
  position: fixed;
  right: v-bind('sidebarCollapsed ? "0px" : sidebarWidth + "px"');
  top: 50%;
  transform: translateY(-50%);
  width: 24px;
  height: 48px;
  background: var(--game-accent-primary);
  color: white;
  border: 2px solid var(--game-border-color);
  border-right: none;
  border-radius: 4px 0 0 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  z-index: 1001;
  transition: right 0.3s ease, background 0.2s ease;
}

.sidebar-toggle:hover {
  background: var(--game-accent-secondary);
}
</style>

<style>
/* Property Drawer - matching left navigation */
.property-drawer {
  background: var(--game-bg-secondary) !important;
  border-left: 3px solid var(--game-accent-primary) !important;
  border-radius: 0 !important;
}

/* Content area */
.property-drawer__content {
  padding: var(--game-spacing-sm);
  overflow-y: auto;
  height: 100%;
}
</style>
