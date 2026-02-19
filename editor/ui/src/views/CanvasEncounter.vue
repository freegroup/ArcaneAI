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
</template>

<script>
import { mapGetters, mapActions } from 'vuex';
import { Splitpanes, Pane } from 'splitpanes';
import 'splitpanes/dist/splitpanes.css';
import StateProperty from './StateProperty.vue';
import StateTriggerProperty from './StateTriggerProperty.vue';
import ConnectionTriggerProperty from './ConnectionTriggerProperty.vue';
import { MessageTypes } from '../../public/shared/SharedConstants.js';
import CCM from '../utils/ContentChangeManager.js';

export default {
  components: {
    Splitpanes,
    Pane,
    StateProperty,
    StateTriggerProperty,
    ConnectionTriggerProperty
  },
  data() {
    return {
      draw2dFrameContent: null,
      paneSize: 50,
      canvasReady: false,
      isCanvasUpdate: false,  // Flag to prevent circular updates from canvas
    };
  },
  computed: {
    ...mapGetters('encounters', ['getEncounterData']),
    ...mapGetters('game', ['gameName']),
    encounterDiagram() {
      // Get encounter data from store (already loaded via fetchEncounters)
      const encounterName = this.$route.params.encounterName;
      if (encounterName) {
        const encounterData = this.getEncounterData(encounterName);
        if (encounterData && encounterData.diagram) {
          // Encounter has structure: { config: {...}, diagram: [...] }
          // Only return the diagram part for canvas
          return encounterData.diagram;
        }
      }
      return null;
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
    ...mapActions('encounters', ['updateEncounter', 'updateEncounterDiagram']),
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
    sendDocumentToCanvas(document) {
      const encounterName = this.$route.params.encounterName || 'unknown';
      this.draw2dFrameContent?.postMessage({ 
        type: MessageTypes.SET_DOCUMENT, 
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
    // Load divider position from local storage on mount
    this.loadDividerPosition();

    // Event listener for messages from the iframe
    this.messageHandler = (event) => {
      if (event.origin !== window.location.origin) return;
      const message = event.data;
      
      // Handle canvas ready message
      if (message.type === MessageTypes.CANVAS_READY) {
        this.updateDraw2dFrame();
        this.canvasReady = true;
        
        // Send current diagram if available
        if (this.encounterDiagram) {
          this.sendDocumentToCanvas(this.encounterDiagram);
        }
      }
      else if (message.type === MessageTypes.DOCUMENT_UPDATED) {
        // No need for blocked flag anymore - updateMapDiagram sets source to 'canvas'
        this.updateMapDiagram(message.data);
      }
      else if (message.type === MessageTypes.CCM) {
        // Bridge: Canvas sends CCM message → forward to ContentChangeManager
        // message.data = { method: 'handleStateChange', payload: {...} }
        const { method, payload } = message.data;
        if (CCM[method] && typeof CCM[method] === 'function') {
          CCM[method]('canvas', payload);
        } else {
          const availableMethods = Object.getOwnPropertyNames(CCM).filter(m => typeof CCM[m] === 'function' && m.startsWith('handle'));
          console.warn(`[CanvasEncounter] Unknown CCM method: "${method}". Available methods: ${availableMethods.join(', ')}`);
        }
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