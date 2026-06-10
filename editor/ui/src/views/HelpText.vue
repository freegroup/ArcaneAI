<template>
  <div class="welcome-wrapper">
    <div class="config-view">
    <div class="welcome-header">
      <div class="welcome-header__title">
        <span>HELP TEXT</span>
        <HelpButton @click="showHelp = true" />
      </div>
    </div>

    <Codemirror
      class="full-height-editor"
      :class="{ 'editor-collapsed': aiAssistExpanded }"
      v-model:value="helpTextValue"
      :options="cmOptions"
      placeholder="Help text for the player — HTML tags like <b>, <i> are allowed..."
    />

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
          <div class="ai-response-area">
            <div v-if="!aiResponse && !aiLoading">
              <AIAssistHelpText />
            </div>

            <AIAssistLoading v-if="aiLoading">AI is working...</AIAssistLoading>

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
            placeholder="e.g. 'Improve readability'"
            @send="improveText"
          />
        </div>
      </transition>
    </div>

    <ExtendedHelpDialog
      v-model="showHelp"
      title="Help Text"
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
import "codemirror/mode/htmlmixed/htmlmixed.js";
import "codemirror/mode/xml/xml.js";
import "codemirror/theme/material-darker.css";

const API_BASE_URL = process.env.VUE_APP_API_BASE_URL;

export default {
  name: 'HelpTextView',
  components: {
    Codemirror, ExtendedHelpDialog, HelpButton, ThemedButton,
    AIAssistLabel, AIAssistHelpText, AIAssistLoading, AIAssistInput
  },
  data() {
    return {
      showHelp: false,
      helpContent: `
<p>The <strong>Help Text</strong> is shown when the player types <code>/help</code>.</p>

<p>Used by the Telegram bot (with HTML parsing) and the console runner (HTML tags are stripped).</p>

<h4>Allowed HTML tags (Telegram):</h4>
<ul>
  <li><code>&lt;b&gt;</code> for bold text</li>
  <li><code>&lt;i&gt;</code> for italics</li>
  <li><code>&lt;code&gt;</code> for monospace</li>
  <li><code>&lt;br&gt;</code> for a line break (in the console becomes a normal newline)</li>
</ul>

<h4>Tips:</h4>
<ul>
  <li><strong>Show examples</strong> — players learn faster from concrete input examples</li>
  <li><strong>Document bot commands</strong> — e.g. <code>/start</code>, <code>/reset</code>, <code>/status</code>, <code>/help</code></li>
  <li><strong>Keep it short</strong> — Telegram has a message-length limit</li>
</ul>
      `,
      cmOptions: {
        mode: "htmlmixed",
        lineNumbers: false,
        lineWrapping: true,
        theme: "material-darker",
        styleActiveLine: false
      },
      aiAssistExpanded: false,
      aiPrompt: '',
      aiResponse: '',
      aiComment: '',
      aiLoading: false,
      wordCountInfo: ''
    }
  },
  computed: {
    ...mapGetters('config', ['helpText']),
    helpTextValue: {
      get() { return this.helpText || '' },
      set(value) { this.setHelpText(value) }
    }
  },
  methods: {
    ...mapActions('config', ['setHelpText']),

    toggleAiAssist() {
      this.aiAssistExpanded = !this.aiAssistExpanded
      if (this.aiAssistExpanded) {
        this.$nextTick(() => {
          if (this.$refs.promptInput) this.$refs.promptInput.focus()
        })
      }
    },

    countWords(text) {
      return text.trim().split(/\s+/).filter(w => w.length > 0).length
    },

    async improveText() {
      if (!this.aiPrompt.trim()) return

      this.aiLoading = true
      this.aiResponse = ''
      this.aiComment = ''
      this.wordCountInfo = ''

      const wordsBefore = this.countWords(this.helpTextValue)

      try {
        const response = await axios.post(`${API_BASE_URL}/text/improve`, {
          text: this.helpTextValue,
          instruction: this.aiPrompt,
          include_comment: true
        })

        const data = response.data
        this.aiResponse = data.improved_text
        this.aiComment = data.comment || ''
        const wordsAfter = this.countWords(data.improved_text)
        this.wordCountInfo = `Words: ${wordsBefore} → ${wordsAfter}`
        this.aiPrompt = ''
      } catch (error) {
        console.error('AI Improve Text Error:', error)
        this.aiResponse = ''
        this.aiComment = 'Error improving text. Please try again.'
      } finally {
        this.aiLoading = false
      }
    },

    applyAiResult() {
      if (this.aiResponse) {
        this.setHelpText(this.aiResponse)
        this.aiResponse = ''
        this.aiComment = ''
        this.aiPrompt = ''
      }
    }
  }
}
</script>

<style scoped>
.welcome-wrapper {
  display: flex;
  flex-direction: column;
  flex: 1;
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
  flex: 1 1 auto;
  position: relative;
  overflow: hidden;
  box-sizing: border-box;
}

.full-height-editor.editor-collapsed {
  flex: 0.6;
}

.full-height-editor >>> .CodeMirror-gutters {
  display: none !important;
}

.full-height-editor >>> .codemirror-container {
  position: absolute;
  top: 0; bottom: 0; left: 0; right: 0;
}

.full-height-editor >>> .CodeMirror {
  position: absolute;
  top: 0; bottom: 0; left: 0; right: 0;
  height: 100%;
}

.ai-assist-header {
  display: flex;
  align-items: center;
  cursor: pointer;
  user-select: none;
}

.expand-enter-active,
.expand-leave-active {
  overflow: hidden;
}
.expand-enter-from,
.expand-leave-to {
  max-height: 0;
}

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
