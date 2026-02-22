<template>
  <div class="config-view">
    <!-- 8-Bit Retro Header -->
    <div class="personality-header">
      <div class="personality-header__title">
        <v-icon class="personality-header__icon">mdi-account-alert</v-icon>
        <span>AI CHARACTER PERSONALITY</span>
        <HelpButton @click="showHelp = true" />
      </div>
    </div>

    <!-- Editor -->
    <Codemirror
      class="full-height-editor"
      :class="{ 'editor-collapsed': aiAssistExpanded }"
      v-model:value="personalityPrompt"
      :options="cmOptions"
      placeholder="Du bist ein Haudegen im 1700 Jahrhundert..."
    />

    <!-- AI Assist Expandable Panel -->
    <div class="ai-assist-panel">
      <div 
        class="ai-assist-header"
        @click="toggleAiAssist"
      >
        <v-icon size="small">{{ aiAssistExpanded ? 'mdi-chevron-up' : 'mdi-chevron-down' }}</v-icon>
        <span class="ai-assist-title">
          <v-icon size="small" color="primary">mdi-robot</v-icon>
          AI Assist
        </span>
      </div>

      <transition name="expand">
        <div v-if="aiAssistExpanded" class="ai-assist-content">
          <!-- Response/Explanation Area -->
          <div class="ai-response-area">
            <div v-if="!aiResponse && !aiLoading" class="ai-helper-text">
              <v-icon size="small" color="primary">mdi-information-outline</v-icon>
              <div>
                <strong>Wie funktioniert AI Assist?</strong>
                <p>Gib der AI eine Anweisung, wie sie deinen Text verbessern soll:</p>
                <ul>
                  <li>"Verbessere die Grammatik und Rechtschreibung"</li>
                  <li>"Übersetze ins Englische"</li>
                  <li>"Mache den Text dramatischer"</li>
                  <li>"Vereinfache die Sprache"</li>
                </ul>
              </div>
            </div>

            <div v-if="aiLoading" class="ai-loading">
              <v-progress-circular indeterminate color="primary" size="20"></v-progress-circular>
              <span>AI arbeitet...</span>
            </div>

            <div v-if="aiResponse" class="ai-result">
              <div class="ai-result-header">
                <strong>Verbesserter Text:</strong>
                <button 
                  @click="applyAiResult" 
                  class="retro-btn retro-btn--sm"
                  title="Text in Editor übernehmen"
                >
                  <v-icon size="small">mdi-check</v-icon>
                  Apply to Editor
                </button>
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

          <!-- Prompt Input -->
          <div class="ai-prompt-input">
            <input
              ref="promptInput"
              v-model="aiPrompt"
              type="text"
              placeholder="z.B. 'Verbessere die Grammatik' oder 'Übersetze ins Englische'"
              @keyup.enter="improveText"
              :disabled="aiLoading"
              class="prompt-field"
            />
            <button 
              @click="improveText" 
              class="retro-btn retro-btn--sm"
              :disabled="!aiPrompt.trim() || aiLoading"
              title="Text verbessern"
            >
              <v-icon size="small">mdi-magic-staff</v-icon>
              Send
            </button>
          </div>
        </div>
      </transition>
    </div>

    <!-- Extended Help Dialog -->
    <ExtendedHelpDialog
      v-model="showHelp"
      title="AI Character Personality"
      :helpText="helpContent"
    />
  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex';
import axios from 'axios';
import ExtendedHelpDialog from '../components/ExtendedHelpDialog.vue';
import HelpButton from '../components/HelpButton.vue';

import Codemirror from "codemirror-editor-vue3";
import "codemirror/addon/display/placeholder.js";
import "codemirror/mode/jinja2/jinja2.js";
import "codemirror/addon/display/placeholder.js";
import "codemirror/theme/juejin.css";
import "codemirror/theme/material-darker.css";

const API_BASE_URL = process.env.VUE_APP_API_BASE_URL;

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
<p>This defines their complete personality!</p>
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
    ...mapGetters('config', ['personality']),
    personalityPrompt: {
      get() {
        return this.personality || '';
      },
      set(value) {
        this.setPersonality(value);
      },
    },
  },
  methods: {
    ...mapActions('config', ['setPersonality']),
    
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
      if (!this.aiPrompt.trim() || !this.personalityPrompt.trim()) {
        return;
      }

      this.aiLoading = true;
      this.aiResponse = '';
      this.aiComment = '';
      this.wordCountInfo = '';

      // Count words before improvement
      const wordsBefore = this.countWords(this.personalityPrompt);

      try {
        const response = await axios.post(`${API_BASE_URL}/text/improve`, {
          text: this.personalityPrompt,
          instruction: this.aiPrompt,
          include_comment: true
        });

        const data = response.data;
        this.aiResponse = data.improved_text;
        this.aiComment = data.comment || '';
        
        // Count words after improvement and create info
        const wordsAfter = this.countWords(data.improved_text);
        this.wordCountInfo = `Wörter: ${wordsBefore} → ${wordsAfter}`;
        
        // Clear prompt after successful response
        this.aiPrompt = '';
      } catch (error) {
        console.error('AI Improve Text Error:', error);
        this.aiResponse = '';
        this.aiComment = 'Fehler bei der Textverbesserung. Bitte versuche es erneut.';
      } finally {
        this.aiLoading = false;
      }
    },

    applyAiResult() {
      if (this.aiResponse) {
        this.setPersonality(this.aiResponse);
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

.ai-assist-title {
  display: flex;
  align-items: center;
  gap: var(--game-spacing-sm);
  font-weight: 600;
  color: var(--game-text-primary);
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

.ai-helper-text {
  display: flex;
  gap: var(--game-spacing-md);
  color: var(--game-text-secondary);
  font-size: 0.9em;
}

.ai-helper-text strong {
  color: var(--game-text-primary);
  display: block;
  margin-bottom: var(--game-spacing-sm);
}

.ai-helper-text p {
  margin: var(--game-spacing-sm) 0;
}

.ai-helper-text ul {
  margin: var(--game-spacing-sm) 0;
  padding-left: 20px;
}

.ai-helper-text li {
  margin: 4px 0;
}

.ai-loading {
  display: flex;
  align-items: center;
  gap: var(--game-spacing-md);
  justify-content: center;
  padding: var(--game-spacing-lg);
  color: var(--game-text-secondary);
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
  font-weight: 600;
  color: var(--game-accent-color);
  font-style: normal;
  margin-bottom: 4px;
}

/* AI Prompt Input */
.ai-prompt-input {
  display: flex;
  gap: var(--game-spacing-sm);
  align-items: center;
}

.prompt-field {
  flex: 1;
  padding: var(--game-spacing-sm) var(--game-spacing-md);
  background: var(--game-bg-primary);
  border: 1px solid var(--game-border-color);
  border-radius: var(--game-radius-sm);
  color: var(--game-text-primary);
  font-size: 0.95em;
  transition: border-color 0.2s;
}

.prompt-field:focus {
  outline: none;
  border-color: var(--game-border-highlight);
}

.prompt-field:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.prompt-field::placeholder {
  color: var(--game-text-muted);
}
</style>