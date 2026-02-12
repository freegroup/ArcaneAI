<template>
  <v-dialog v-model="isOpen" max-width="900px" persistent>
    <v-card class="jinja-editor-dialog">
      <v-card-title class="dialog-title">
        <v-icon class="title-icon">mdi-code-braces</v-icon>
        Scene Description Editor
        <v-spacer></v-spacer>
        <button @click="cancel" class="retro-btn retro-btn--icon">
          ✕
        </button>
      </v-card-title>

      <v-card-text class="dialog-content">
        <MonacoEditor
          v-model:value="editedText"
          language="jinja2"
          :options="editorOptions"
          class="monaco-editor"
          @editorDidMount="handleEditorDidMount"
        />
      </v-card-text>

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
import MonacoEditor from 'monaco-editor-vue3';
import * as monaco from 'monaco-editor';

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
    MonacoEditor
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
      }
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
    }
  },
  watch: {
    modelValue(newVal) {
      if (newVal) {
        // Dialog opened - initialize with current text
        this.editedText = this.text;
      }
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

.dialog-title {
  background: linear-gradient(135deg, var(--game-bg-tertiary) 0%, #1a1a2e 100%) !important;
  color: var(--game-accent-secondary) !important;
  font-family: var(--game-font-family-retro) !important;
  font-size: 20px !important;
  font-weight: 700 !important;
  text-transform: uppercase !important;
  letter-spacing: 3px !important;
  padding: var(--game-spacing-lg) !important;
  border-bottom: 3px solid var(--game-accent-primary) !important;
  border-top: 3px solid var(--game-accent-secondary) !important;
  display: flex !important;
  align-items: center !important;
  gap: var(--game-spacing-sm) !important;
  text-shadow: 2px 2px 0px rgba(0, 0, 0, 0.8), 
               0 0 10px var(--game-accent-secondary) !important;
  box-shadow: inset 0 -3px 0 rgba(0, 0, 0, 0.3) !important;
}

.title-icon {
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
</style>