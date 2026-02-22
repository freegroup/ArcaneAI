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

    <!-- Property Sidebar with toggle -->
    <div class="sidebar-panel" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
      <button class="sidebar-toggle" @click="toggleSidebar" :title="sidebarCollapsed ? 'Expand panel' : 'Collapse panel'">
        {{ sidebarCollapsed ? '◀' : '▶' }}
      </button>
      <div class="sidebar-content" v-show="!sidebarCollapsed">
        <EncounterPropertyView v-if="draw2dFrameContent" :draw2dFrame="draw2dFrameContent"/>
        <StateProperty v-if="draw2dFrameContent" :draw2dFrame="draw2dFrameContent"/>
        <StateTriggerProperty v-if="draw2dFrameContent" :draw2dFrame="draw2dFrameContent"/>
        <ConnectionTriggerProperty v-if="draw2dFrameContent" :draw2dFrame="draw2dFrameContent"/>
      </div>
    </div>
  
    <!-- Chat Dialog -->
    <ChatDialog 
      v-model="showChatDialog" 
      :stateName="chatDialogStateName"
    />
    
    <!-- Add Encounter Dialog -->
    <EncounterNewDialog v-model="showEncounterDialog" />
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
      showEncounterDialog: false,
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
    '$route.query.addEncounter': {
      immediate: true,
      handler(value) {
        if (value === 'true') {
          this.showEncounterDialog = true;
          this.$router.replace({ query: {} });
        }
      }
    }
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
    
    // Set draw2dFrameContent immediately when iframe ref is available
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
/* Vuetify Best Practice: Use flex with explicit height */
.canvas-game-container {
  display: flex;
  flex: 1 1 auto;
  height: 100%;
  min-height: 0;
  width: 100%;
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

.sidebar-panel {
  width: 350px;
  flex-shrink: 0;
  border-left: 1px solid var(--game-border-color);
  background: var(--game-bg-secondary);
  display: flex;
  flex-direction: column;
}

/* Breite Monitore (≥1440px): Doppelt so breites Sidebar */
@media (min-width: 1440px) {
  .sidebar-panel {
    width: 600px;
  }
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
}

/* Sidebar needs position relative for toggle button */
.sidebar-panel {
  position: relative;
  transition: width 0.3s ease;
  overflow: visible;
}

/* Sidebar Toggle Button */
.sidebar-toggle {
  position: absolute;
  left: -24px;
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
  z-index: 100;
  transition: background 0.2s ease;
}

.sidebar-toggle:hover {
  background: var(--game-accent-secondary);
}

/* Collapsed state - minimal width for toggle button visibility */
.sidebar-collapsed {
  width: 0 !important;
  min-width: 0 !important;
  border-left: none !important;
}
</style>
