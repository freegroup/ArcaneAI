<template>
  <div class="config-view">
    <!-- 8-Bit Retro Header -->
    <div class="personality-header">
      <div class="personality-header__title">
        <v-icon class="personality-header__icon">mdi-account-alert</v-icon>
        <span>AI CHARACTER IDENTITY</span>
        <v-icon 
          class="personality-header__info"
          @click="showHelp = true"
        >
          mdi-information
        </v-icon>
      </div>
    </div>

    <!-- Editor -->
    <Codemirror
      class="full-height-editor"
      v-model:value="normalPrompt"
      :options="cmOptions"
      placeholder="Du bist ein Haudegen im 1700 Jahrhundert..."
    />

    <!-- Extended Help Dialog -->
    <ExtendedHelpDialog
      v-model="showHelp"
      title="AI Character Identity"
      :helpText="helpContent"
    />
  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex';
import ExtendedHelpDialog from '../components/ExtendedHelpDialog.vue';

import Codemirror from "codemirror-editor-vue3";
import "codemirror/addon/display/placeholder.js";
import "codemirror/mode/jinja2/jinja2.js";
import "codemirror/addon/display/placeholder.js";
import "codemirror/theme/juejin.css";
import "codemirror/theme/material-darker.css";

export default {
  name: 'PropertyView',
  components: { 
    Codemirror,
    ExtendedHelpDialog
  },
  data(){
    return {
      showHelp: false,
      helpContent: `
Define how your AI game companion behaves:

• Their personality & language style
• Length of their responses
• How they interact with you
• Their behavior in the game world

This defines their complete identity!
      `,
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
  width: 100%;
  overflow-y: auto;
  padding: 0;
  box-sizing: border-box; 
  display: flex;
  flex-direction: column;
  background: var(--game-bg-secondary);
}

/* 8-Bit Retro Header */
.personality-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--game-spacing-lg);
  background: linear-gradient(135deg, var(--game-bg-tertiary) 0%, #1a1a2e 100%);
  border-bottom: 3px solid var(--game-accent-primary);
  border-top: 2px solid var(--game-accent-secondary);
  box-shadow: inset 0 -2px 0 rgba(0, 0, 0, 0.3);
}

.personality-header__title {
  display: flex;
  align-items: center;
  gap: var(--game-spacing-md);
  color: var(--game-accent-secondary);
  font-family: var(--game-font-family-retro);
  font-size: 16px;
  text-transform: uppercase;
  letter-spacing: 2px;
  text-shadow: 2px 2px 0px rgba(0, 0, 0, 0.8),
               0 0 10px var(--game-accent-secondary);
}

.personality-header__icon {
  color: var(--game-accent-secondary);
  font-size: 32px;
  filter: drop-shadow(0 0 8px var(--game-accent-secondary));
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    filter: drop-shadow(0 0 8px var(--game-accent-secondary));
  }
  50% {
    transform: scale(1.05);
    filter: drop-shadow(0 0 12px var(--game-accent-secondary));
  }
}

.personality-header__info {
  color: var(--game-text-secondary);
  font-size: 24px;
  cursor: pointer;
  transition: all var(--game-transition-fast);
}

.personality-header__info:hover {
  color: var(--game-accent-secondary);
  filter: drop-shadow(0 0 8px var(--game-accent-secondary));
  transform: scale(1.1);
}

.full-height-editor {
  flex: 1; 
  height: 100%;
  margin: var(--game-spacing-md);
}

.full-height-editor >>> .CodeMirror {
  font-size: 18px;
  font-family: var(--game-font-family-mono) !important;
  background: var(--game-bg-primary) !important;
  border: 2px solid var(--game-border-color);
  border-radius: var(--game-radius-md);
  height: 100%;
  line-height: 1.6;
}

.full-height-editor >>> .CodeMirror-gutters {
  display: none !important;
}

.full-height-editor >>> .CodeMirror-placeholder {
  color: var(--game-text-muted) !important;
  font-style: italic;
}
</style>
