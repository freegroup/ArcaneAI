<template>
  <div class="config-view">
    <!-- 8-Bit Retro Header -->
    <div class="personality-header">
      <div class="personality-header__title">
        <v-icon class="personality-header__icon">mdi-account-alert</v-icon>
        <span>AI CHARACTER IDENTITY</span>
        <HelpButton @click="showHelp = true" />
      </div>
    </div>

    <!-- Editor -->
    <Codemirror
      class="full-height-editor"
      v-model:value="identityPrompt"
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
import HelpButton from '../components/HelpButton.vue';

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
    ExtendedHelpDialog,
    HelpButton
  },
  data(){
    return {
      showHelp: false,
      helpContent: `
<p>Define how your AI game companion behaves:</p>
<ul>
  <li><strong>Personality & language style</strong> - How they talk and express themselves</li>
  <li><strong>Response length</strong> - Short and snappy or detailed descriptions</li>
  <li><strong>Interaction style</strong> - Friendly, mysterious, grumpy, etc.</li>
  <li><strong>Game world behavior</strong> - Their role in the story</li>
</ul>
<p>This defines their complete identity!</p>
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
    ...mapGetters('games', ['gameConfig']),
    mapConfig() {
      return this.gameConfig;
    },
    identityPrompt: {
      get() {
        return this.mapConfig.identity;
      },
      set(value) {
        // Commit the updated system prompt to the store
        this.updateGameConfig({ ...this.mapConfig, identity: value });
      },
    },
    
  },
  methods: {
    ...mapActions('games', ['updateGameConfig']),
    updateMapConfig(config) {
      this.updateGameConfig(config);
    },
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
  padding: var(--screen-wide-header-padding-y, var(--game-spacing-lg)) var(--game-spacing-lg);
  background: linear-gradient(135deg, var(--game-bg-tertiary) 0%, #1a1a2e 100%);
  border-bottom: 3px solid var(--game-accent-primary);
  border-top: 2px solid var(--game-accent-secondary);
  box-shadow: inset 0 -2px 0 rgba(0, 0, 0, 0.3);
}

.personality-header__title {
  display: flex;
  align-items: center;
  gap: var(--screen-wide-header-gap, var(--game-spacing-md));
  color: var(--game-accent-secondary);
  font-family: var(--game-font-family-retro);
  font-size: var(--screen-wide-header-font-size, 16px);
  letter-spacing: var(--screen-wide-header-letter-spacing, 2px);
  text-shadow: 2px 2px 0px rgba(0, 0, 0, 0.8),
               0 0 10px var(--game-accent-secondary);
}

.personality-header__icon {
  color: var(--game-accent-secondary);
  font-size: var(--screen-wide-header-icon-size, 32px);
  filter: drop-shadow(0 0 8px var(--game-accent-secondary));
  animation: pulse 2s ease-in-out infinite;
}

/* Responsive header for laptop screens (60% height) */
@media (max-width: 1439px) {
  .personality-header {
    padding: var(--screen-medium-header-padding-y) var(--game-spacing-lg);
  }
  
  .personality-header__title {
    font-size: var(--screen-medium-header-font-size);
    gap: var(--screen-medium-header-gap);
    letter-spacing: var(--screen-medium-header-letter-spacing);
  }
  
  .personality-header__icon {
    font-size: var(--screen-medium-header-icon-size);
  }
  
  .personality-header__info {
    font-size: var(--screen-medium-header-info-size);
  }
}

/* Responsive header for small screens */
@media (max-width: 1023px) {
  .personality-header {
    padding: var(--screen-small-header-padding-y) var(--game-spacing-md);
  }
  
  .personality-header__title {
    font-size: var(--screen-small-header-font-size);
    gap: var(--screen-small-header-gap);
    letter-spacing: var(--screen-small-header-letter-spacing);
  }
  
  .personality-header__icon {
    font-size: var(--screen-small-header-icon-size);
  }
  
  .personality-header__info {
    font-size: var(--screen-small-header-info-size);
  }
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
  font-size: var(--screen-wide-header-info-size, 24px);
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
