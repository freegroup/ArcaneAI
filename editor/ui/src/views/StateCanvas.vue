<template>
  <splitpanes 
      id="state-editor"
      ref="splitPanes" 
      class="default-theme full-height"  
      @resized="handleResize">
    <!-- Editor-Bereich -->
    <pane min-size="40%"  :size="paneSize">
      <div  class="iframe-container">
        <iframe
          ref="draw2dFrame"
          src="/canvas/index.html"
          frameborder="0"
          style="width: 100%; height: 100%; border: none"
        ></iframe>
      </div>
    </pane>

    <!-- Sidebar-Bereich -->
    <pane min-size="20%"  :size="100-paneSize" class="scroll-y">
      <PropertyViewState v-if="draw2dFrameContent" :draw2dFrame="draw2dFrameContent"/>
      <PropertyViewTriggerLabel v-if="draw2dFrameContent" :draw2dFrame="draw2dFrameContent"/>
      <PropertyViewTriggerConnection v-if="draw2dFrameContent" :draw2dFrame="draw2dFrameContent"/>
    </pane>
  </splitpanes>
</template>

<script>
import { mapGetters, mapActions } from 'vuex';
import { Splitpanes, Pane } from 'splitpanes';
import 'splitpanes/dist/splitpanes.css';
import PropertyViewState from './PropertyViewState.vue';
import PropertyViewTriggerLabel from './PropertyViewTriggerLabel.vue';
import PropertyViewTriggerConnection from './PropertyViewTriggerConnection.vue';
import MessageTypes from '../../public/canvas/MessageTypes.js';

export default {
  components: {
    Splitpanes,
    Pane,
    PropertyViewState,
    PropertyViewTriggerLabel,
    PropertyViewTriggerConnection
  },
  data() {
    return {
      draw2dFrameContent: null,
      paneSize: 50,
      canvasReady: false,
      pendingDocument: null,
    };
  },
  computed: {
    ...mapGetters('maps', ['mapDiagram', 'documentRequestTrigger', 'mapName', 'updateSource']),
    draw2dFrame() {
      return this.$refs.draw2dFrame;
    }
  },
  watch: {
    mapDiagram: {
      handler(newMapDiagram) {
        // Check if update came from canvas - if so, skip sending back
        if(this.updateSource === 'canvas'){
          return;
        }

        // Use helper method which handles ready state (includes checks)
        if (newMapDiagram) {
          this.sendDocumentToCanvas(newMapDiagram);
        }
      },
      // Don't use immediate - let canvasReady message trigger the initial send
      immediate: false,
    }
  },
  methods: {
    ...mapActions('maps', ['saveMap', 'updateMapDiagram']),

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
      // Only send if canvas is ready
      if (!this.canvasReady) {
        this.pendingDocument = document;
        return;
      }
      
      if (!this.draw2dFrameContent) {
        return;
      }
      
      // Extra safety check for draw2dFrame ref
      if (!this.draw2dFrame || !this.draw2dFrame.contentWindow) {
        return;
      }
      
      const iframe = this.draw2dFrame.contentWindow;
      iframe.postMessage({ type: MessageTypes.SET_DOCUMENT, data: JSON.parse(JSON.stringify(document)) }, '*');
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
    window.addEventListener('message', (event) => {
      if (event.origin !== window.location.origin) return;
      const message = event.data;
      
      // Handle canvas ready message
      if (message.type === MessageTypes.CANVAS_READY) {
        this.canvasReady = true;
        this.updateDraw2dFrame();
        
        // Send pending document if any
        if (this.pendingDocument) {
          this.sendDocumentToCanvas(this.pendingDocument);
          this.pendingDocument = null;
        } else if (this.mapDiagram) {
          // Or send current diagram if available
          this.sendDocumentToCanvas(this.mapDiagram);
        }
      }
      else if (message.type === MessageTypes.DOCUMENT_UPDATED) {
        // No need for blocked flag anymore - updateMapDiagram sets source to 'canvas'
        this.updateMapDiagram(message.data);
      }
      else if(message.type === MessageTypes.TOGGLE_FULLSCREEN){
        var element = document.getElementById('state-editor');

        var requestFullScreen =
          element.requestFullscreen ||
          element.mozRequestFullScreen ||
          element.webkitRequestFullscreen ||
          element.msRequestFullscreen;

        var cancelFullScreen =
          document.exitFullscreen ||
          document.mozCancelFullScreen ||
          document.webkitExitFullscreen ||
          document.msExitFullscreen;

        if (
          !document.fullscreenElement &&
          !document.mozFullScreenElement &&
          !document.webkitFullscreenElement &&
          !document.msFullscreenElement
        ) {
          requestFullScreen.call(element);
        } else {
          cancelFullScreen.call(document);
        }
      }
    });
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