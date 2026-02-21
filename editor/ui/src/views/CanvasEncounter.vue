<template>
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
          src="/encounter/index.html"
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

  <!-- Import State Dialog -->
  <ImportStateDialog v-model="showImportStateDialog" />
</template>

<script>
import { mapGetters, mapActions } from 'vuex';
import { Splitpanes, Pane } from 'splitpanes';
import 'splitpanes/dist/splitpanes.css';
import StateProperty from './StateProperty.vue';
import StateTriggerProperty from './StateTriggerProperty.vue';
import ConnectionTriggerProperty from './ConnectionTriggerProperty.vue';
import ImportStateDialog from '../components/ImportStateDialog.vue';
import { MessageTypes } from '../../public/shared/SharedConstants.js';
import ViewComposer from '../utils/ViewComposer.js';

export default {
  components: {
    Splitpanes,
    Pane,
    StateProperty,
    StateTriggerProperty,
    ConnectionTriggerProperty,
    ImportStateDialog
  },
  // Accept route params as props (passed via router with props: true)
  props: {
    gameName: {
      type: String,
      default: null
    },
    encounterName: {
      type: String,
      default: null
    }
  },
  data() {
    return {
      draw2dFrameContent: null,
      paneSize: 50,
      canvasReady: false,
      isCanvasUpdate: false,  // Flag to prevent circular updates from canvas
      showImportStateDialog: false,
    };
  },
  computed: {
    ...mapGetters('model', ['allStates', 'allConnections']),
    ...mapGetters('views', ['currentView']),
    
    /**
     * View-ID für den aktuellen Encounter
     */
    currentViewId() {
      const encounterName = this.$route.params.encounterName;
      return encounterName ? `encounter_${encounterName}` : null;
    },
    
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
    
    draw2dFrame() {
      return this.$refs.draw2dFrame;
    }
  },
  watch: {
    /**
     * Watch for composed diagram changes from Model+View.
     * 
     * Note: Canvas updates are ignored using isCanvasUpdate flag.
     * PropertyEditor updates are ignored using model.isPropertyUpdate flag
     * to prevent circular updates that would clear the selection.
     */
    composedDiagram: {
      handler(newDiagram) {
        if (newDiagram && this.canvasReady) {
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
    ...mapActions('model', ['setModel', 'mergeModel', 'saveModel']),
    ...mapActions('views', ['updateCurrentViewLayout', 'saveView', 'setCurrentView', 'createEncounterView', 'removeStateFromCurrentView', 'removeConnectionFromCurrentView']),
    
    /**
     * Speichert Model und aktuelle View
     */
    async saveMap() {
      try {
        await this.saveModel();
        await this.saveView({ viewId: this.currentViewId });
      } catch (error) {
        console.error('[CanvasEncounter] Save failed:', error);
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
      
      // Gelöschte States entfernen - NUR aus der View, NICHT aus dem Model!
      // (Encounter-View: State wird nur aus dem View-Layout entfernt, bleibt im Model)
      for (const stateId of previousLayoutIds) {
        if (!currentCanvasStateIds.includes(stateId)) {
          this.removeStateFromCurrentView(stateId);
        }
      }
      
      // Gelöschte Connections entfernen - NUR aus der View, NICHT aus dem Model!
      for (const connId of previousRouteIds) {
        if (!currentCanvasConnIds.includes(connId)) {
          this.removeConnectionFromCurrentView(connId);
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
      if (this.$refs.draw2dFrame) {
        this.draw2dFrameContent = this.$refs.draw2dFrame.contentWindow;
      }
    },
    
    /**
     * Send document to canvas via parent window postMessage.
     */
    sendDocumentToCanvas(document) {
      const encounterName = this.$route.params.encounterName || 'unknown';
      window.postMessage({ 
        type: MessageTypes.V2C_SET_DOCUMENT, 
        data: JSON.parse(JSON.stringify(document)),
        source: `vue:encounter:${encounterName}`
      }, '*');
    },
    
    handleResize(event) {
      this.paneSize = event[0].size;
      localStorage.setItem('paneSize', this.paneSize);
    },
    
    loadDividerPosition() {
      const savedSize = localStorage.getItem('paneSize');
      if (savedSize !== null) {
        this.paneSize = parseFloat(savedSize);
      }
    },
    
    /**
     * Initialisiert die View für diesen Encounter
     */
    async initEncounterView() {
      const encounterName = this.$route.params.encounterName;
      if (!encounterName) return;
      
      const viewId = `encounter_${encounterName}`;
      
      // Prüfe ob View existiert, sonst erstelle sie
      const existingView = this.$store.getters['views/viewById'](viewId);
      if (!existingView) {
        this.createEncounterView({ encounterName });
      }
      
      // Setze aktuelle View
      this.setCurrentView(viewId);
    }
  },
  mounted() {
    // Initialize encounter view (Overlay Pattern)
    this.initEncounterView();

    // Load divider position from local storage on mount
    this.loadDividerPosition();

    // Event listener for messages
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
          // Skip if this is a response to a property update (setShapeData)
          // The model was already updated by PropertyEditor's updateState()
          if (message.source === 'canvas:setShapeData') {
            return;
          }
          this.handleCanvasUpdate(message.data);
          break;

        case MessageTypes.C2V_OPEN_IMPORT_DIALOG:
          this.showImportStateDialog = true;
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
    if (this.messageHandler) {
      window.removeEventListener('message', this.messageHandler);
    }
  }
};
</script>

<style scoped>
.full-height {
  height: 100vh;
  display: flex;
}

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