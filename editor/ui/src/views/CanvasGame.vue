<template>
  <div class="canvas-game-container">
    <splitpanes 
        id="canvas-game"
        ref="splitPanes" 
        class="default-theme full-height"  
        @resized="handleResize">
    <!-- Editor-Bereich -->
    <pane min-size="40%"  :size="paneSize">
      <div  class="iframe-container">
        <iframe
          ref="draw2dFrame"
          src="/game/index.html"
          frameborder="0"
          style="width: 100%; height: 100%; border: none"
        ></iframe>
      </div>
    </pane>

    <!-- Sidebar-Bereich -->
    <pane min-size="20%"  :size="100-paneSize" class="scroll-y">
      <StateProperty v-if="draw2dFrameContent" :draw2dFrame="draw2dFrameContent"/>
      <StateTriggerProperty v-if="draw2dFrameContent" :draw2dFrame="draw2dFrameContent"/>
      <ConnectionTriggerProperty v-if="draw2dFrameContent" :draw2dFrame="draw2dFrameContent"/>
    </pane>
  </splitpanes>
  
    <!-- Chat Dialog - outside splitpanes to avoid layout issues -->
    <ChatDialog 
      v-model="showChatDialog" 
      :stateName="chatDialogStateName"
    />
  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex';
import { Splitpanes, Pane } from 'splitpanes';
import 'splitpanes/dist/splitpanes.css';
import StateProperty from './StateProperty.vue';
import StateTriggerProperty from './StateTriggerProperty.vue';
import ConnectionTriggerProperty from './ConnectionTriggerProperty.vue';
import ChatDialog from '../components/ChatDialog.vue';
import { MessageTypes } from '../../public/shared/SharedConstants.js';
import ViewComposer from '../utils/ViewComposer.js';

export default {
  components: {
    Splitpanes,
    Pane,
    StateProperty,
    StateTriggerProperty,
    ConnectionTriggerProperty,
    ChatDialog
  },
  data() {
    return {
      draw2dFrameContent: null,
      paneSize: 50,
      canvasReady: false,
      isCanvasUpdate: false,  // Flag to prevent circular updates from canvas
      showChatDialog: false,
      chatDialogStateName: ''
    };
  },
  computed: {
    ...mapGetters('game', ['gameName']),
    ...mapGetters('model', ['allStates', 'allConnections']),
    ...mapGetters('views', ['currentView']),
    
    /**
     * Komponiertes Diagram für Canvas (Model + View Layout)
     * Verwendet das Overlay Pattern: Model-Daten + View-Layout = draw2d Diagram
     */
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
    /**
     * Watch for composed diagram changes.
     * 
     * Triggers when:
     * 1. Model changes (states/connections added/removed/modified)
     * 2. View changes (layouts/routes changed)
     * 
     * Note: Canvas updates are ignored using isCanvasUpdate flag.
     * PropertyEditor updates are ignored using model.isPropertyUpdate flag
     * to prevent circular updates that would clear the selection.
     */
    composedDiagram: {
      handler(newDiagram) {
        if (newDiagram && this.canvasReady) {
          // Skip if this change came from the canvas itself
          if (this.isCanvasUpdate) {
            return;
          }
          // Skip if this change came from PropertyEditor
          // PropertyEditor uses updateState which sets model.isPropertyUpdate
          if (this.$store.state.model.isPropertyUpdate) {
            return;
          }
          this.sendDocumentToCanvas(newDiagram);
        }
      },
      deep: true,
      immediate: false,
    }
  },
  methods: {
    ...mapActions('model', ['setModel', 'mergeModel', 'removeState', 'removeConnection', 'saveModel']),
    ...mapActions('views', ['updateCurrentViewLayout', 'saveView', 'setCurrentView']),
    
    /**
     * Speichert Model und aktuelle View
     */
    async saveMap() {
      try {
        await this.saveModel();
        await this.saveView({ viewId: 'world' });
      } catch (error) {
        console.error('[CanvasGame] Save failed:', error);
        throw error;
      }
    },
    
    /**
     * Verarbeitet Diagram-Updates vom Canvas.
     * Trennt Model-Daten von Layout-Daten und speichert separat.
     * 
     * WICHTIG: Verwendet mergeModel statt setModel, damit States aus anderen
     * Views nicht verloren gehen (Overlay Pattern).
     */
    handleCanvasUpdate(diagram) {
      this.isCanvasUpdate = true;
      
      // 1. Extrahiere was im Canvas ist
      const newModel = ViewComposer.extractModel(diagram);
      const newLayout = ViewComposer.extractLayout(diagram);
      
      // 2. Finde gelöschte Elemente
      // WICHTIG: Vergleiche mit dem Model, nicht mit der View!
      // Ein State gilt als gelöscht wenn:
      // - Er im Model existiert UND
      // - Er in dieser View ein Layout hatte UND  
      // - Er jetzt nicht mehr im Canvas ist
      const currentView = this.currentView;
      const previousLayoutIds = Object.keys(currentView?.stateLayouts || {});
      const currentCanvasStateIds = Object.keys(newModel.states);
      const previousRouteIds = Object.keys(currentView?.connectionRoutes || {});
      const currentCanvasConnIds = Object.keys(newModel.connections);
      
      // Gelöschte States entfernen (hatten Layout in dieser View, sind nicht mehr im Canvas)
      for (const stateId of previousLayoutIds) {
        if (!currentCanvasStateIds.includes(stateId)) {
          // Prüfe ob State noch im Model existiert (könnte schon gelöscht sein)
          if (this.$store.state.model.states[stateId]) {
            this.removeState(stateId);
          }
        }
      }
      
      // Gelöschte Connections entfernen
      for (const connId of previousRouteIds) {
        if (!currentCanvasConnIds.includes(connId)) {
          if (this.$store.state.model.connections[connId]) {
            this.removeConnection(connId);
          }
        }
      }
      
      // 3. Model-Änderungen mergen (nicht überschreiben!)
      this.mergeModel(newModel);
      
      // 4. Layout-Änderungen für diese View speichern
      this.updateCurrentViewLayout(newLayout);
      
      this.$nextTick(() => {
        this.isCanvasUpdate = false;
      });
    },

    async saveReceivedDocument() {
      await this.saveMap();
    },
    
    updateDraw2dFrame() {
      // Check if the draw2dFrame ref is set
      if (this.$refs.draw2dFrame) {
        this.draw2dFrameContent = this.$refs.draw2dFrame.contentWindow;
      }
    },
    
    /**
     * Send document to canvas via parent window postMessage.
     * Uses unified message architecture: both Vue and Canvas communicate
     * through the parent window. Canvas listens on window.parent.
     */
    sendDocumentToCanvas(document) {
      window.postMessage({ 
        type: MessageTypes.V2C_SET_DOCUMENT, 
        data: JSON.parse(JSON.stringify(document)),
        source: 'vue:world'
      }, '*');
    },
    
    handleResize(event) {
      this.paneSize = event[0].size;
      localStorage.setItem('paneSize', this.paneSize);
    },
    
    loadDividerPosition() {
      // Load pane size from local storage
      const savedSize = localStorage.getItem('paneSize');
      if (savedSize !== null) {
        this.paneSize = parseFloat(savedSize);
      }
    },
  },
  mounted() {
    // Set current view to 'world' for this canvas
    this.setCurrentView('world');
    
    // Load divider position from local storage on mount
    this.loadDividerPosition();

    // Event listener for messages (unified architecture: all messages go through parent window)
    this.messageHandler = (event) => {
      if (event.origin !== window.location.origin) return;
      const message = event.data;
      
      // Message Router: Handle C2V messages, forward V2C messages to canvas
      switch (message.type) {
        case MessageTypes.C2V_CANVAS_READY:
          this.updateDraw2dFrame();
          this.canvasReady = true;
          // Send current diagram if available
          if (this.composedDiagram && this.composedDiagram.length > 0) {
            this.sendDocumentToCanvas(this.composedDiagram);
          }
          break;

        case MessageTypes.C2V_DOCUMENT_UPDATED:
          // Diagram vom Canvas erhalten - in Model und Layout aufteilen
          this.handleCanvasUpdate(message.data);
          break;

        case MessageTypes.C2V_CHAT_FROM_HERE:
          // Open chat dialog with selected state
          this.chatDialogStateName = message.stateName;
          this.showChatDialog = true;
          break;

        default:
          // Forward V2C messages to the iframe (Vue → Canvas)
          if (message.type?.startsWith('v2c:') && this.draw2dFrameContent) {
            this.draw2dFrameContent.postMessage(message, '*');
          }
          break;
      }
    };
    window.addEventListener('message', this.messageHandler);
  },
  beforeUnmount() {
    // Clean up message listener
    if (this.messageHandler) {
      window.removeEventListener('message', this.messageHandler);
    }
  }
};
</script>

<style scoped>
.canvas-game-container {
  height: 100vh;
  width: 100%;
}

.full-height {
  height: 100%;
  display: flex;
}

/* Ensure each pane inside splitpanes takes full height */
.splitpanes {
  height: 100%;
  display: flex;
}
.splitpanes.default-theme .splitpanes__pane {
  background-color: transparent;
  overflow-y: auto;
}

.iframe-container {
  width: 100%;
  height: 100%;
  display: flex;
}

iframe {
  width: 100%;
  height: 100%;
  border: none;
}
</style>