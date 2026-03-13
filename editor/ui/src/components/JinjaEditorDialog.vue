<template>
  <v-dialog v-model="isOpen" max-width="900px" persistent>
    <v-card class="jinja-editor-dialog">
      <!-- Dialog Header -->
      <DialogHeader
        title="Scene Description Editor"
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
          <AIAssistLabel />
        </div>

        <transition name="expand">
          <div v-if="aiAssistExpanded" class="ai-assist-content">
            <!-- Response/Explanation Area -->
            <div class="ai-response-area">
            <div v-if="!aiResponse && !aiLoading">
              <AIAssistHelpText>
                <template #footer>
                  <p class="jinja-note">
                    <v-icon size="x-small">mdi-shield-check</v-icon>
                    Alle Jinja-Tags bleiben erhalten!
                  </p>
                </template>
              </AIAssistHelpText>
            </div>

                <AIAssistLoading v-if="aiLoading">AI arbeitet...</AIAssistLoading>

              <div v-if="aiResponse" class="ai-result">
                <div class="ai-result-header">
                  <strong>Verbesserter Text:</strong>
                <ThemedButton 
                  @click="applyAiResult" 
                  title="Text in Editor übernehmen"
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
              placeholder="z.B. 'Verbessere die Grammatik' oder 'Übersetze ins Englische'"
              @send="improveText"
            />
          </div>
        </transition>
      </div>

      <!-- Editor Action Bar -->
      <v-card-actions class="dialog-actions">
        <v-spacer></v-spacer>
        <ThemedButton @click="cancel" variant="secondary">
          Cancel
        </ThemedButton>
        <ThemedButton @click="save">
          Save
        </ThemedButton>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import axios from 'axios';
import MonacoEditor from 'monaco-editor-vue3';
import * as monaco from 'monaco-editor';
import DialogHeader from './DialogHeader.vue';
import ThemedButton from './ThemedButton.vue';
import AIAssistLabel from './AIAssistLabel.vue';
import AIAssistHelpText from './AIAssistHelpText.vue';
import AIAssistLoading from './AIAssistLoading.vue';
import AIAssistInput from './AIAssistInput.vue';

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
    DialogHeader,
    ThemedButton,
    AIAssistLabel,
    AIAssistHelpText,
    AIAssistLoading,
    AIAssistInput
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
        console.log('[JinjaEditorDialog] Dialog opened, text prop:', this.text?.substring(0, 50));
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
    // Also watch text prop to sync when it changes after dialog opens
    text: {
      handler(newVal) {
        console.log('[JinjaEditorDialog] text prop changed:', newVal?.substring(0, 50));
        if (this.modelValue && !this.editedText) {
          // Dialog is open but editedText is empty - sync from text prop
          console.log('[JinjaEditorDialog] Syncing empty editedText from text prop');
          this.editedText = newVal;
          this.lastSavedText = newVal;
        }
      },
      immediate: true
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
      console.log('improveText called', {
        aiPrompt: this.aiPrompt,
        editedText: this.editedText?.substring(0, 50),
        API_BASE_URL
      });
      
      // Only require prompt - text can be empty (AI will generate new content)
      if (!this.aiPrompt.trim()) {
        console.log('improveText early return - empty prompt');
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
.dialog-content {
  padding: 0;
  overflow: hidden;
}

.monaco-editor {
  width: 100%;
  height: 100%;
}

/* Editor Toolbar */
.editor-toolbar {
  display: flex;
}

.toolbar-btn {
  cursor: not-allowed;
  position: relative;
}

.toolbar-btn:not(:disabled) {
  cursor: pointer;
}

/* Undo/Redo Icons */
.undo-icon {
  display: inline-block;
}

.redo-icon {
  display: inline-block;
  transform: scaleX(-1);
}

/* AI Assist Panel */
.ai-assist-header {
  display: flex;
  align-items: center;
  cursor: pointer;
  user-select: none;
}

/* Expand transition */
.expand-enter-active,
.expand-leave-active {
  overflow: hidden;
}

/* AI Response Area */
.ai-response-area {
  overflow-y: auto;
}

.jinja-note {
  display: flex;
  align-items: center;
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
  font-style: italic;
}

.word-count-info {
  font-style: normal;
}
</style>
