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
    <pane min-size="20%"  :size="100-paneSize">
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
          console.log('🚫 [SYNC] Vuex → Canvas: BLOCKED (update came from canvas, preventing loop)');
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
        console.log('⏳ [SYNC] Canvas not ready yet, queueing document');
        this.pendingDocument = document;
        return;
      }
      
      if (!this.draw2dFrameContent) {
        console.warn('⚠️ [SYNC] draw2dFrameContent not available');
        return;
      }
      
      // Extra safety check for draw2dFrame ref
      if (!this.draw2dFrame || !this.draw2dFrame.contentWindow) {
        console.warn('⚠️ [SYNC] draw2dFrame ref not available yet');
        return;
      }
      
      console.log('📤 [SYNC] Sending document to canvas', {
        diagramItemCount: document?.length || 0
      });
      const iframe = this.draw2dFrame.contentWindow;
      iframe.postMessage({ type: 'setDocument', data: JSON.parse(JSON.stringify(document)) }, '*');
    },
    handleResize(event) {
      this.paneSize = event[0].size;
      localStorage.setItem('paneSize', this.paneSize);
      console.log(this.paneSize)
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
      if (message.type === 'canvasReady') {
        console.log('✅ [SYNC] Canvas is ready, iframe fully loaded');
        this.canvasReady = true;
        this.updateDraw2dFrame();
        
        // Send pending document if any
        if (this.pendingDocument) {
          console.log('📤 [SYNC] Sending queued document to canvas');
          this.sendDocumentToCanvas(this.pendingDocument);
          this.pendingDocument = null;
        }
        // Or send current diagram if available
        else if (this.mapDiagram) {
          this.sendDocumentToCanvas(this.mapDiagram);
        }
      }
      else if (message.type === 'updateDocumentData') {
        console.log('🔄 [SYNC] Canvas → Vuex: Document updated from canvas', {
          diagramItemCount: message.data?.length || 0
        });
        // No need for blocked flag anymore - updateMapDiagram sets source to 'canvas'
        this.updateMapDiagram(message.data)
      }
      else if(message.type === "toggleFullScreen"){
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
