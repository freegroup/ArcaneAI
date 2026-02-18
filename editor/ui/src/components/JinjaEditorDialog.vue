<template>
  <v-dialog v-model="isOpen" max-width="900px" persistent>
    <v-card class="jinja-editor-dialog">
      <!-- Dialog Header -->
      <DialogHeader 
        title="Scene Description Editor" 
        icon="mdi-code-braces"
        @close="cancel" 
      />

      <!-- Editor Toolbar -->
      <div class="editor-toolbar">
        <button 
          class="toolbar-btn" 
          :disabled="!canUndo"
          @click="undo"
          title="Undo (Ctrl+Z)"
        >
          <span class="undo-icon">↵</span>
        </button>
        <button 
          class="toolbar-btn" 
          :disabled="!canRedo"
          @click="redo"
          title="Redo (Ctrl+Shift+Z)"
        >
          <span class="redo-icon">↵</span>
        </button>
      </div>

      <!-- Jinja Editor -->
      <v-card-text class="dialog-content" :style="{ height: editorHeight }">
        <MonacoEditor
          v-model:value="editedText"
          language="jinja2"
          :options="editorOptions"
          class="monaco-editor"
          @editorDidMount="handleEditorDidMount"
        />
      </v-card-text>

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
                  <p class="jinja-note">
                    <v-icon size="x-small">mdi-shield-check</v-icon>
                    Alle Jinja-Tags bleiben erhalten!
                  </p>
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

      <!-- Editor Action Bar -->
      <v-card-actions class="dialog-actions">
        <v-spacer></v-spacer>
        <button @click="cancel" class="retro-btn retro-btn--secondary retro-btn--sm">
          Cancel
        </button>
        <button @click="save" class="retro-btn retro-btn--sm">
          Save
        </button>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import axios from 'axios';
import MonacoEditor from 'monaco-editor-vue3';
import * as monaco from 'monaco-editor';
import DialogHeader from './DialogHeader.vue';

const API_BASE_URL = process.env.VUE_APP_API_BASE_URL;

// Register Jinja2 language
monaco.languages.register({ id: 'jinja2' });

monaco.languages.setMonarchTokensProvider('jinja2', {
  tokenizer: {
    root: [

    // Jinja2 comments
      [/\{#/, 'comment', '@comment'],
      // Jinja2 statements
      [/\{%/, 'delimiter.jinja', '@statement'],
      // Jinja2 expressions
      [/\{\{/, 'delimiter.jinja', '@expression'],
      // Everything else is text
      [/./, 'text'],
    ],
    comment: [
      [/#\}/, 'comment', '@pop'],
      [/./, 'comment'],
    ],
    statement: [
      [/%\}/, 'delimiter.jinja', '@pop'],
      [/\b(if|elif|else|endif|for|endfor|block|endblock|extends|include|macro|endmacro|set|raw|endraw)\b/, 'keyword'],
      [/\b(in|not|and|or|is)\b/, 'operator'],
      [/"([^"\\]|\\[\s\S])*"/, 'string'],
      [/'([^'\\]|\\[\s\S])*'/, 'string'],
      [/\d+/, 'number'],
      [/[<>=!]+/, 'operator'],
      [/[\w.]+/, 'variable'],
      [/./, 'text'],
    ],
    expression: [
      [/\}\}/, 'delimiter.jinja', '@pop'],
      [/"([^"\\]|\\[\s\S])*"/, 'string'],
      [/'([^'\\]|\\[\s\S])*'/, 'string'],
      [/\d+/, 'number'],
      [/[\w.]+/, 'variable'],
      [/./, 'text'],
    ],
  },
});

// Define theme colors for Jinja2
monaco.editor.defineTheme('jinja2-dark', {
  base: 'vs-dark',
  inherit: true,
  rules: [
    { token: 'delimiter.jinja', foreground: 'C586C0', fontStyle: 'bold' },
    { token: 'keyword', foreground: 'C586C0' },
    { token: 'operator', foreground: 'D4D4D4' },
    { token: 'variable', foreground: '9CDCFE' },
    { token: 'string', foreground: 'CE9178' },
    { token: 'number', foreground: 'B5CEA8' },
    { token: 'comment', foreground: '6A9955', fontStyle: 'italic' },
    { token: 'text', foreground: 'D4D4D4' },
  ],
  colors: {},
});

export default {
  name: 'JinjaEditorDialog',
  components: {
    MonacoEditor,
    DialogHeader
  },
  props: {
    modelValue: {
      type: Boolean,
      default: false
    },
    text: {
      type: String,
      default: ''
    }
  },
  data() {
    return {
      editedText: '',
      editor: null,
      editorOptions: {
        theme: 'jinja2-dark',
        minimap: { enabled: false },
        lineNumbers: 'off',
        wordWrap: 'on',
        scrollBeyondLastLine: false,
        fontSize: 16,
        fontFamily: 'Consolas, Monaco, "Courier New", monospace',
        padding: { top: 10, bottom: 10 },
        automaticLayout: false,
        // Disable suggestions
        quickSuggestions: false,
        suggestOnTriggerCharacters: false,
      },
      // AI Assist state
      aiAssistExpanded: false,
      aiPrompt: '',
      aiResponse: '',
      aiComment: '',
      aiLoading: false,
      wordCountInfo: '',
      // Undo/Redo state
      undoStack: [],
      redoStack: [],
      debounceTimer: null,
      debounceDelay: 500, // ms - delay before pushing to history
      isUndoRedoOperation: false, // flag to prevent history updates during undo/redo
      lastSavedText: '', // track text for debouncing
      isInitializing: false // flag to prevent history updates during initialization
    };
  },
  computed: {
    isOpen: {
      get() {
        return this.modelValue;
      },
      set(value) {
        this.$emit('update:modelValue', value);
      }
    },
    editorHeight() {
      // Adjust editor height based on AI assist panel state
      return this.aiAssistExpanded ? '300px' : '500px';
    },
    canUndo() {
      return this.undoStack.length > 0;
    },
    canRedo() {
      return this.redoStack.length > 0;
    }
  },
  watch: {
    modelValue(newVal) {
      if (newVal) {
        // Dialog opened - initialize with current text and history
        this.isInitializing = true;
        this.editedText = this.text;
        this.lastSavedText = this.text;
        this.undoStack = [];
        this.redoStack = [];
        // Reset initialization flag after initial render
        this.$nextTick(() => {
          this.isInitializing = false;
        });
      }
    },
    editedText(newVal) {
      // Skip if this is an undo/redo operation or initialization
      if (this.isUndoRedoOperation || this.isInitializing) {
        return;
      }

      // Debounce history updates
      if (this.debounceTimer) {
        clearTimeout(this.debounceTimer);
      }

      // Store the state that we want to save (before the change started)
      const stateToSave = this.lastSavedText;

      this.debounceTimer = setTimeout(() => {
        // Only push to history if text actually changed from last saved state
        if (stateToSave !== newVal) {
          this.undoStack.push(stateToSave);
          this.redoStack = []; // Clear redo stack on new change
          this.lastSavedText = newVal;
        }
      }, this.debounceDelay);
    }
  },
  methods: {
    handleEditorDidMount(editor) {
      this.editor = editor;
      // Focus the editor after mount
      this.$nextTick(() => {
        if (this.editor) {
          this.editor.focus();
        }
      });
    },

    save() {
      this.$emit('save', this.editedText);
      this.isOpen = false;
    },

    cancel() {
      this.isOpen = false;
    },

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
      if (!this.aiPrompt.trim() || !this.editedText.trim()) {
        return;
      }

      this.aiLoading = true;
      this.aiResponse = '';
      this.aiComment = '';
      this.wordCountInfo = '';

      // Count words before improvement
      const wordsBefore = this.countWords(this.editedText);

      try {
        const response = await axios.post(`${API_BASE_URL}/text/improve`, {
          text: this.editedText,
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
        this.editedText = this.aiResponse;
        // Clear AI response after applying
        this.aiResponse = '';
        this.aiComment = '';
        this.aiPrompt = '';
      }
    },

    // Undo/Redo methods
    undo() {
      if (this.undoStack.length === 0) {
        return;
      }

      // Get previous state from undo stack
      const previousText = this.undoStack.pop();
      
      // Push current state to redo stack
      this.redoStack.push(this.editedText);
      
      // Set flag to prevent watcher from adding to history
      this.isUndoRedoOperation = true;
      this.editedText = previousText;
      this.lastSavedText = previousText;
      
      // Reset flag after update
      this.$nextTick(() => {
        this.isUndoRedoOperation = false;
      });
    },

    redo() {
      if (this.redoStack.length === 0) {
        return;
      }

      // Get next state from redo stack
      const nextText = this.redoStack.pop();
      
      // Push current state to undo stack
      this.undoStack.push(this.editedText);
      
      // Set flag to prevent watcher from adding to history
      this.isUndoRedoOperation = true;
      this.editedText = nextText;
      this.lastSavedText = nextText;
      
      // Reset flag after update
      this.$nextTick(() => {
        this.isUndoRedoOperation = false;
      });
    },

    handleKeyDown(event) {
      // Ctrl+Z for Undo
      if (event.ctrlKey && event.key === 'z' && !event.shiftKey) {
        event.preventDefault();
        this.undo();
      }
      // Ctrl+Shift+Z for Redo
      else if (event.ctrlKey && event.shiftKey && event.key === 'z') {
        event.preventDefault();
        this.redo();
      }
      // Cmd+Z for Undo (Mac)
      else if (event.metaKey && event.key === 'z' && !event.shiftKey) {
        event.preventDefault();
        this.undo();
      }
      // Cmd+Shift+Z for Redo (Mac)
      else if (event.metaKey && event.shiftKey && event.key === 'z') {
        event.preventDefault();
        this.redo();
      }
    }
  },
  mounted() {
    // Add keyboard shortcuts
    window.addEventListener('keydown', this.handleKeyDown);
  },
  beforeUnmount() {
    // Clean up keyboard shortcuts
    window.removeEventListener('keydown', this.handleKeyDown);
    // Clear debounce timer
    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer);
    }
  }
};
</script>

<style scoped>
/* Override Vuetify defaults */
.jinja-editor-dialog :deep(.v-card) {
  background: var(--game-bg-secondary) !important;
  color: var(--game-text-primary) !important;
}

.jinja-editor-dialog {
  background: var(--game-bg-secondary);
  color: var(--game-text-primary);
  border: 2px solid var(--game-border-highlight);
  border-radius: var(--game-radius-lg);
  box-shadow: var(--game-shadow-lg);
}


.dialog-content {
  padding: 0;
  height: 500px;
  overflow: hidden;
  background: var(--game-bg-secondary);
}

.monaco-editor {
  width: 100%;
  height: 100%;
}

.dialog-actions {
  padding: var(--game-spacing-lg);
  border-top: 1px solid var(--game-border-color);
  background: var(--game-bg-tertiary);
}

.dialog-actions .retro-btn {
  margin-left: var(--game-spacing-md);
}

/* Editor Toolbar */
.editor-toolbar {
  display: flex;
  gap: var(--game-spacing-sm);
  padding: var(--game-spacing-sm) var(--game-spacing-md);
  background: var(--game-bg-tertiary);
  border-bottom: 1px solid var(--game-border-color);
}

.toolbar-btn {
  background: var(--game-bg-secondary);
  border: 3px solid var(--game-border-color);
  padding: 6px 8px;
  cursor: not-allowed;
  opacity: 0.5;
  border-radius: 0; /* Eckiger Rahmen für 8-bit Look */
  color: var(--game-text-secondary);
  font-family: 'Press Start 2P', 'Courier New', monospace;
  font-size: 10px;
  transition: all 0.1s ease;
  box-shadow: 3px 3px 0 rgba(0, 0, 0, 0.5);
  position: relative;
}

.toolbar-btn:not(:disabled) {
  cursor: pointer;
  opacity: 1;
  color: var(--game-text-primary);
  background: var(--game-bg-primary);
  border-color: var(--game-border-highlight);
}

.toolbar-btn:not(:disabled):hover {
  background: var(--game-accent-color);
  border-color: var(--game-accent-color);
  color: var(--game-bg-primary);
  transform: translate(1px, 1px);
  box-shadow: 2px 2px 0 rgba(0, 0, 0, 0.5);
}

.toolbar-btn:not(:disabled):active {
  transform: translate(3px, 3px);
  box-shadow: none;
}

/* Undo/Redo Icons */
.undo-icon {
  display: inline-block;
  font-size: 32px;
  line-height: 0.5;
}

.redo-icon {
  display: inline-block;
  font-size: 32px;
  line-height: 0.5;
  transform: scaleX(-1); /* Horizontale Spiegelung für Redo */
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

.jinja-note {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: var(--game-spacing-sm);
  padding: var(--game-spacing-sm);
  background: var(--game-bg-secondary);
  border-radius: var(--game-radius-sm);
  font-size: 0.85em;
  color: var(--game-accent-color);
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
