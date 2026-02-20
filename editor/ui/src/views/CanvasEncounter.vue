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
import CCM from '../utils/ContentChangeManager.js';

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
    ...mapGetters('encounters', ['currentEncounter', 'currentEncounterName', 'currentEncounterDiagram', 'getEncounterData']),
    encounterDiagram() {
      // Use currentEncounterDiagram getter (based on currentEncounterName)
      return this.currentEncounterDiagram;
    },
    draw2dFrame() {
      return this.$refs.draw2dFrame;
    }
  },
  watch: {
    /**
     * Watch for diagram changes from the Store.
     * 
     * This is needed for INITIAL LOADING when:
     * 1. Canvas is ready (CANVAS_READY received)
     * 2. But the diagram wasn't loaded yet from the server
     * 3. Later, the Store loads the diagram from API
     * 4. This watcher sends it to the canvas
     * 
     * Note: Canvas updates are ignored using isCanvasUpdate flag
     * to prevent circular updates that would clear the selection.
     */
    encounterDiagram: {
      handler(newDiagram) {
        if (newDiagram && this.canvasReady) {
          // Skip if this change came from the canvas itself
          if (this.isCanvasUpdate) {
            this.isCanvasUpdate = false;  // Reset flag
            return;
          }
          this.sendDocumentToCanvas(newDiagram);
        }
      },
      immediate: false,
    }
  },
  methods: {
    ...mapActions('encounters', ['updateEncounter', 'updateEncounterDiagram', 'setCurrentEncounter', 'clearCurrentEncounter']),
    async saveMap() {
      // Save encounter, not game
      const encounterName = this.$route.params.encounterName;
      const gameName = this.$route.params.gameName;
      if (encounterName && gameName) {
        const encounterData = this.getEncounterData(encounterName);
        if (encounterData) {
          await this.updateEncounter({ gameName, encounterName, data: encounterData });
        }
      }
    },
    updateMapDiagram(diagramData) {
      const encounterName = this.$route.params.encounterName;
      if (encounterName) {
        this.isCanvasUpdate = true;  // Set flag before store update
        this.updateEncounterDiagram({ encounterName, diagram: diagramData });
      }
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
      // Load pane size from local storage
      const savedSize = localStorage.getItem('paneSize');
      if (savedSize !== null) {
        this.paneSize = parseFloat(savedSize);
      }
    },
  },
  mounted() {
    // Set current encounter in store
    const encounterName = this.$route.params.encounterName;
    if (encounterName) {
      this.setCurrentEncounter(encounterName);
    }

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
          if (this.encounterDiagram) {
            this.sendDocumentToCanvas(this.encounterDiagram);
          }
          break;

        case MessageTypes.C2V_DOCUMENT_UPDATED:
          this.updateMapDiagram(message.data);
          break;

        case MessageTypes.C2V_CCM: {
          // Bridge: Canvas sends CCM message → forward to ContentChangeManager
          const { method, payload } = message.data;
          if (CCM[method] && typeof CCM[method] === 'function') {
            CCM[method]('canvas', payload);
          } else {
            const availableMethods = Object.getOwnPropertyNames(CCM).filter(m => typeof CCM[m] === 'function' && m.startsWith('handle'));
            console.warn(`[CanvasEncounter] Unknown CCM method: "${method}". Available methods: ${availableMethods.join(', ')}`);
          }
          break;
        }

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
    // Clear current encounter in store
    this.clearCurrentEncounter();
    
    // Clean up message listener
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