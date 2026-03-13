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
                <ThemedButton 
                  @click="applyAiResult" 
                  title="Apply text to editor"
                >
                  <v-icon size="small">mdi-check</v-icon>
                  Apply to Editor
                </ThemedButton>
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
import ThemedButton from '../components/ThemedButton.vue';
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
    ThemedButton,
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
/* Wrapper - full height of parent */
.welcome-wrapper {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-sizing: border-box;
}

.config-view {
  flex: 1;
  overflow: hidden;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

/* 8-Bit Retro Header */
.welcome-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.welcome-header__title {
  display: flex;
  align-items: center;
}

.full-height-editor {
  flex: 1;
  overflow: hidden;
  box-sizing: border-box;
}

.full-height-editor.editor-collapsed {
  flex: 0.6;
}

.full-height-editor >>> .CodeMirror-gutters {
  display: none !important;
}

/* AI Assist Panel */
.ai-assist-panel {
}

.ai-assist-header {
  display: flex;
  align-items: center;
  cursor: pointer;
  user-select: none;
}

.ai-assist-content {
}

/* Expand transition */
.expand-enter-active,
.expand-leave-active {
  overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
  max-height: 0;
}

/* AI Response Area */
.ai-response-area {
  overflow-y: auto;
}

.ai-result {
  display: flex;
  flex-direction: column;
}

.ai-result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.ai-result-text {
  white-space: pre-wrap;
  word-wrap: break-word;
}

.ai-comment {
  display: flex;
  align-items: flex-start;
}
</style>