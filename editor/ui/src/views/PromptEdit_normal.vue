<template>
  <div class="config-view" >
    <!-- System Prompt Section -->
    <h4>Normal State Prompt</h4>
    <Codemirror
      class="full-height-editor"
      v-model:value="normalPrompt"
      :options="cmOptions"
      placeholder="test placeholder"
  />
  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex';

import Codemirror from "codemirror-editor-vue3";
import "codemirror/addon/display/placeholder.js";
import "codemirror/mode/jinja2/jinja2.js";
import "codemirror/addon/display/placeholder.js";
import "codemirror/theme/juejin.css";
import "codemirror/theme/material-darker.css";

export default {
  name: 'PropertyView',
  components: { Codemirror },
  data(){
    return {
      cmOptions: {
        mode: "jinja2",
        lineNumbers: false, 
        lineWrapping: true, 
        theme: "material-darker",
        styleActiveLine: false,
      }
    }
  },
  computed: {
    ...mapGetters('maps', ['mapConfig']),
    normalPrompt: {
      get() {
        return this.mapConfig.normal_prompt;
      },
      set(value) {
        // Commit the updated system prompt to the store
        this.updateMapConfig({ ...this.mapConfig, normal_prompt: value });
      },
    },
    
  },
  methods: {
    ...mapActions('maps', ['updateMapConfig']),
    onChange: (val, cm) => {
      console.log(val);
      console.log(cm.getValue());
    }
  },
};
</script>

<style scoped>
.config-view {
  height: 100%;
  width:100%;
  overflow-y: auto;
  padding: 10px;
  box-sizing: border-box; 
  display: flex;
  flex-direction: column;
}

.full-height-editor {
  flex: 1; 
  height: 100%; 
}

.full-height-editor >>> .CodeMirror {
  font-size: 16px; /* Hier kannst du die Schriftgröße anpassen */
  font-family: 'Roboto', Arial, Helvetica, sans-serif !important;
}

.full-height-editor >>> .CodeMirror-gutters {
  display: none !important; /* Versteckt den gesamten Gutter-Bereich */
}
</style>
