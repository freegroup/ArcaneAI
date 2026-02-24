<template>
  <div class="welcome-wrapper">
    <div class="config-view">
    <!-- 8-Bit Retro Header -->
    <div class="welcome-header">
      <div class="welcome-header__title">
        <span>WELCOME PROMPT</span>
        <HelpButton @click="showHelp = true" />
      </div>
    </div>

    <!-- Editor -->
    <Codemirror
      class="full-height-editor"
      :class="{ 'editor-collapsed': aiAssistExpanded }"
      v-model:value="welcomePromptText"
      :options="cmOptions"
      placeholder="Set the scene for the player when the game starts..."
    />

    <!-- AI Assist Expandable Panel -->
    <div class="ai-assist-panel">
      <div 
        class="ai-assist-header"
        @click="toggleAiAssist"
      >
        <v-icon size="small">{{ aiAssistExpanded ? 'mdi-chevron-up' : 'mdi-chevron-down' }}</v-icon>
        <AIAssistLabel />
      </div>

      <transition name="expand">
        <div v-if="aiAssistExpanded" class="ai-assist-content">
          <!-- Response/Explanation Area -->
          <div class="ai-response-area">
            <div v-if="!aiResponse && !aiLoading">
              <AIAssistHelpText />
            </div>

            <AIAssistLoading v-if="aiLoading" />

            <div v-if="aiResponse" class="ai-result">
              <div class="ai-result-header">
                <strong>Improved Text:</strong>
                <RetroButton 
                  @click="applyAiResult" 
                  title="Apply text to editor"
                >
                  <v-icon size="small">mdi-check</v-icon>
                  Apply to Editor
                </RetroButton>
              </div>
              <div class="ai-result-text">{{ aiResponse }}</div>
              <div v-if="aiComment || wordCountInfo" class="ai-comment">
                <v-icon size="small" color="info">mdi-comment-text-outline</v-icon>
                <div>
                  <div v-if="wordCountInfo" class="word-count-info">{{ wordCountInfo }}</div>
                  <div v-if="aiComment">{{ aiComment }}</div>
                </div>
              </div>
            </div>
          </div>

          <AIAssistInput
            ref="promptInput"
            v-model="aiPrompt"
            :loading="aiLoading"
            placeholder="e.g. 'Make it more atmospheric' or 'Translate to German'"
            @send="improveText"
          />
        </div>
      </transition>
    </div>

    <!-- Extended Help Dialog -->
    <ExtendedHelpDialog
      v-model="showHelp"
      title="Welcome Prompt"
      :helpText="helpContent"
    />
    </div>
  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex';
import axios from 'axios';
import ExtendedHelpDialog from '../components/ExtendedHelpDialog.vue';
import HelpButton from '../components/HelpButton.vue';
import RetroButton from '../components/RetroButton.vue';
import AIAssistLabel from '../components/AIAssistLabel.vue';
import AIAssistHelpText from '../components/AIAssistHelpText.vue';
import AIAssistLoading from '../components/AIAssistLoading.vue';
import AIAssistInput from '../components/AIAssistInput.vue';

import Codemirror from "codemirror-editor-vue3";
import "codemirror/addon/display/placeholder.js";
import "codemirror/mode/jinja2/jinja2.js";
import "codemirror/addon/display/placeholder.js";
import "codemirror/theme/juejin.css";
import "codemirror/theme/material-darker.css";

const API_BASE_URL = process.env.VUE_APP_API_BASE_URL;

export default {
  name: 'WelcomePromptView',
  components: { 
    Codemirror,
    ExtendedHelpDialog,
    HelpButton,
    RetroButton,
    AIAssistLabel,
    AIAssistHelpText,
    AIAssistLoading,
    AIAssistInput
  },
  data(){
    return {
      showHelp: false,
      helpContent: `
<p>The <strong>Welcome Prompt</strong> is sent to the AI when the game starts.</p>

<p>This text tells the AI what scene to describe to the player as their first impression of the game world.</p>

<h4>What to include:</h4>
<ul>
  <li><strong>Setting the scene</strong> - Describe the environment the player wakes up in</li>
  <li><strong>Atmosphere</strong> - Sounds, smells, lighting, mood</li>
  <li><strong>Initial situation</strong> - What just happened? Why is the player here?</li>
  <li><strong>Call to action</strong> - What should the player do first?</li>
</ul>

<h4>Tips:</h4>
<ul>
  <li>Keep it concise - the AI will elaborate</li>
  <li>Use present tense for immediacy</li>
  <li>Appeal to multiple senses</li>
  <li>Create intrigue or urgency</li>
</ul>

<h4>Example:</h4>
<p><em>"Describe the player waking up in a dark tavern cellar. They hear muffled voices above and smell spilled ale. A single candle flickers nearby, revealing a locked door."</em></p>
      `,
      cmOptions: {
        mode: "jinja2",
        lineNumbers: false, 
        lineWrapping: true, 
        theme: "material-darker",
        styleActiveLine: false,
      },
      // AI Assist state
      aiAssistExpanded: false,
      aiPrompt: '',
      aiResponse: '',
      aiComment: '',
      aiLoading: false,
      wordCountInfo: ''
    }
  },
  computed: {
    ...mapGetters('config', ['welcomePrompt']),
    welcomePromptText: {
      get() {
        return this.welcomePrompt || '';
      },
      set(value) {
        this.setWelcomePrompt(value);
      },
    },
  },
  methods: {
    ...mapActions('config', ['setWelcomePrompt']),
    
    // AI Assist methods
    toggleAiAssist() {
      this.aiAssistExpanded = !this.aiAssistExpanded;
      
      // Focus the prompt input after expansion
      if (this.aiAssistExpanded) {
        this.$nextTick(() => {
          if (this.$refs.promptInput) {
            this.$refs.promptInput.focus();
          }
        });
      }
    },

    countWords(text) {
      // Simple word count - split by whitespace and filter empty strings
      return text.trim().split(/\s+/).filter(word => word.length > 0).length;
    },

    async improveText() {
      // Only require prompt - text can be empty (AI will generate new content)
      if (!this.aiPrompt.trim()) {
        return;
      }

      this.aiLoading = true;
      this.aiResponse = '';
      this.aiComment = '';
      this.wordCountInfo = '';

      // Count words before improvement
      const wordsBefore = this.countWords(this.welcomePromptText);

      try {
        const response = await axios.post(`${API_BASE_URL}/text/improve`, {
          text: this.welcomePromptText,
          instruction: this.aiPrompt,
          include_comment: true
        });

        const data = response.data;
        this.aiResponse = data.improved_text;
        this.aiComment = data.comment || '';
        
        // Count words after improvement and create info
        const wordsAfter = this.countWords(data.improved_text);
        this.wordCountInfo = `Words: ${wordsBefore} → ${wordsAfter}`;
        
        // Clear prompt after successful response
        this.aiPrompt = '';
      } catch (error) {
        console.error('AI Improve Text Error:', error);
        this.aiResponse = '';
        this.aiComment = 'Error improving text. Please try again.';
      } finally {
        this.aiLoading = false;
      }
    },

    applyAiResult() {
      if (this.aiResponse) {
        this.setWelcomePrompt(this.aiResponse);
        // Clear AI response after applying
        this.aiResponse = '';
        this.aiComment = '';
        this.aiPrompt = '';
      }
    }
  },
};
</script>

<style scoped>
/* Wrapper wie CanvasGame - volle Höhe des Parents */
.welcome-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-sizing: border-box;
}

.config-view {
  flex: 1;
  min-height: 0; /* WICHTIG: Erlaubt zu schrumpfen */
  width: 100%;
  max-width: 100%; /* Verhindert Überlauf */
  overflow: hidden; /* Kein Scrolling am Container - nur intern */
  padding: var(--game-spacing-md); /* Padding statt margin am Editor */
  padding-top: 0; /* Header braucht kein extra padding oben */
  box-sizing: border-box; 
  display: flex;
  flex-direction: column;
  background: var(--game-bg-secondary);
}

/* 8-Bit Retro Header */
.welcome-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--screen-wide-header-padding-y, var(--game-spacing-lg)) var(--game-spacing-lg);
  background: linear-gradient(135deg, var(--game-bg-tertiary) 0%, #1a1a2e 100%);
  border-bottom: 3px solid var(--game-accent-primary);
  border-top: 2px solid var(--game-accent-secondary);
  box-shadow: inset 0 -2px 0 rgba(0, 0, 0, 0.3);
}

.welcome-header__title {
  display: flex;
  align-items: center;
  gap: var(--screen-wide-header-gap, var(--game-spacing-md));
  color: var(--game-accent-secondary);
  font-family: var(--game-font-family-retro);
  font-size: var(--screen-wide-header-font-size, 16px);
  letter-spacing: var(--screen-wide-header-letter-spacing, 2px);
}

/* Responsive header for laptop screens (60% height) */
@media (max-width: 1439px) {
  .welcome-header {
    padding: var(--screen-medium-header-padding-y) var(--game-spacing-lg);
  }
  
  .welcome-header__title {
    font-size: var(--screen-medium-header-font-size);
    gap: var(--screen-medium-header-gap);
    letter-spacing: var(--screen-medium-header-letter-spacing);
  }
  
  .welcome-header__info {
    font-size: var(--screen-medium-header-info-size);
  }
}

/* Responsive header for small screens */
@media (max-width: 1023px) {
  .welcome-header {
    padding: var(--screen-small-header-padding-y) var(--game-spacing-md);
  }
  
  .welcome-header__title {
    font-size: var(--screen-small-header-font-size);
    gap: var(--screen-small-header-gap);
    letter-spacing: var(--screen-small-header-letter-spacing);
  }
  
  .welcome-header__info {
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

.welcome-header__info {
  color: var(--game-text-secondary);
  font-size: var(--screen-wide-header-info-size, 24px);
  cursor: pointer;
  transition: all var(--game-transition-fast);
}

.welcome-header__info:hover {
  color: var(--game-accent-secondary);
  filter: drop-shadow(0 0 8px var(--game-accent-secondary));
  transform: scale(1.1);
}

.full-height-editor {
  flex: 1; 
  min-height: 0; /* WICHTIG: Erlaubt dem flex-item zu schrumpfen */
  overflow: hidden; /* Content scrollt im CodeMirror */
  margin: 0; /* Kein margin - padding ist am Container */
  margin-top: var(--game-spacing-md); /* Nur oben Abstand zum Header */
  width: 100%;
  box-sizing: border-box;
  transition: flex 0.3s ease;
}

.full-height-editor.editor-collapsed {
  flex: 0.6;
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

/* AI Assist Panel */
.ai-assist-panel {
  margin-top: auto;
  border-top: 1px solid var(--game-border-color);
  background: var(--game-bg-tertiary);
}

.ai-assist-header {
  display: flex;
  align-items: center;
  gap: var(--game-spacing-sm);
  padding: var(--game-spacing-md);
  cursor: pointer;
  user-select: none;
  transition: background-color 0.2s;
}

.ai-assist-header:hover {
  background: var(--game-bg-hover);
}

.ai-assist-content {
  padding: var(--game-spacing-md);
  background: var(--game-bg-secondary);
}

/* Expand transition */
.expand-enter-active,
.expand-leave-active {
  transition: all 0.3s ease;
  max-height: 400px;
  overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
  max-height: 0;
  opacity: 0;
}

/* AI Response Area */
.ai-response-area {
  min-height: 120px;
  max-height: 200px;
  overflow-y: auto;
  margin-bottom: var(--game-spacing-md);
  padding: var(--game-spacing-md);
  background: var(--game-bg-primary);
  border: 1px solid var(--game-border-color);
  border-radius: var(--game-radius-md);
}

.ai-result {
  display: flex;
  flex-direction: column;
  gap: var(--game-spacing-sm);
}

.ai-result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--game-spacing-sm);
}

.ai-result-text {
  padding: var(--game-spacing-md);
  background: var(--game-bg-secondary);
  border: 1px solid var(--game-border-highlight);
  border-radius: var(--game-radius-sm);
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 0.95em;
  line-height: 1.5;
}

.ai-comment {
  display: flex;
  align-items: flex-start;
  gap: var(--game-spacing-sm);
  padding: var(--game-spacing-sm);
  background: var(--game-bg-tertiary);
  border-left: 3px solid var(--game-accent-color);
  border-radius: var(--game-radius-sm);
  font-size: 0.9em;
  color: var(--game-text-secondary);
  font-style: italic;
}

.word-count-info {
  color: var(--game-accent-color);
  font-style: normal;
  margin-bottom: 4px;
}
</style>