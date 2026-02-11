<template>
  <v-dialog v-model="isOpen" max-width="900px" persistent>
    <v-card class="jinja-editor-dialog">
      <v-card-title class="dialog-title">
        <v-icon class="title-icon">mdi-code-braces</v-icon>
        Scene Description Editor
        <v-spacer></v-spacer>
        <v-btn icon size="small" @click="cancel">
          <v-icon>mdi-close</v-icon>
        </v-btn>
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
        <v-btn @click="cancel" class="cancel-btn">
          Cancel
        </v-btn>
        <v-spacer></v-spacer>
        <v-btn @click="save" class="save-btn">
          Save Changes
        </v-btn>
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
.jinja-editor-dialog {
  background: var(--game-bg-secondary);
  color: var(--game-text-primary);
  border: 2px solid var(--game-border-highlight);
  border-radius: var(--game-radius-lg);
}

.dialog-title {
  background: var(--game-bg-tertiary);
  color: var(--game-accent-secondary);
  font-size: var(--game-font-size-lg);
  font-weight: 600;
  padding: var(--game-spacing-lg);
  border-bottom: 1px solid var(--game-border-color);
  display: flex;
  align-items: center;
  gap: var(--game-spacing-sm);
}

.title-icon {
  color: var(--game-accent-secondary);
  font-size: 28px;
}

.dialog-title :deep(.v-btn) {
  background: transparent;
  color: var(--game-text-secondary);
}

.dialog-title :deep(.v-btn:hover) {
  background: var(--game-input-hover);
  color: var(--game-text-primary);
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

.cancel-btn {
  background: var(--game-bg-secondary);
  color: var(--game-text-primary);
  border: 1px solid var(--game-border-color);
  font-weight: 600;
  padding: var(--game-spacing-sm) var(--game-spacing-xl);
  border-radius: var(--game-radius-md);
  transition: all var(--game-transition-fast);
}

.cancel-btn:hover {
  background: var(--game-input-hover);
  border-color: var(--game-border-highlight);
}

.save-btn {
  background: var(--game-accent-primary);
  color: var(--game-text-primary);
  font-weight: 600;
  padding: var(--game-spacing-sm) var(--game-spacing-xl);
  border-radius: var(--game-radius-md);
  transition: all var(--game-transition-fast);
}

.save-btn:hover {
  background: var(--game-accent-tertiary);
  box-shadow: var(--game-shadow-glow);
  transform: translateY(-2px);
}
</style>