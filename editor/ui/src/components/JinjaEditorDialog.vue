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
        <Codemirror
          ref="cmEditor"
          class="code-editor"
          v-model:value="editedText"
          :options="cmOptions"
          placeholder="Enter scene description with Jinja2 syntax..."
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
import Codemirror from "codemirror-editor-vue3";
import "codemirror/addon/display/placeholder.js";
import "codemirror/mode/jinja2/jinja2.js";
import "codemirror/theme/material-darker.css";

export default {
  name: 'JinjaEditorDialog',
  components: { Codemirror },
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
      cmOptions: {
        mode: "jinja2",
        lineNumbers: false,
        lineWrapping: true,
        theme: "default",
        styleActiveLine: false,
        indentUnit: 2,
        tabSize: 2,
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
        // Set focus to editor and refresh after dialog opens
        this.$nextTick(() => {
          if (this.$refs.cmEditor && this.$refs.cmEditor.cminstance) {
            // Refresh CodeMirror to recalculate dimensions
            this.$refs.cmEditor.cminstance.refresh();
            // Then set focus
            this.$refs.cmEditor.cminstance.focus();
          }
        });
      }
    }
  },
  methods: {
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
  overflow: auto;
  background: var(--game-bg-secondary);
}

.code-editor {
  height: 100%;
}

/* CodeMirror Game Theme - EXAKT wie PropertyViewState */
.code-editor :deep(.CodeMirror) {
  font-size: var(--game-font-size-md);
  font-family: var(--game-font-family-mono);
  background: var(--game-bg-secondary);
  color: var(--game-text-primary);
  border: 1px solid var(--game-input-border);
  border-radius: var(--game-radius-md);
  padding: var(--game-spacing-sm);
  min-height: 120px;
}

.code-editor :deep(.CodeMirror-gutters) {
  display: none;
}

.code-editor :deep(.CodeMirror-cursor) {
  border-left-color: var(--game-accent-primary);
}

.code-editor :deep(.CodeMirror-selected) {
  background: rgba(233, 69, 96, 0.2);
}

/* Jinja2 Syntax Highlighting */
.code-editor :deep(.cm-variable-2) {
  color: #ffa07a;
}

.code-editor :deep(.cm-keyword) {
  color: #f39c12;
}

.code-editor :deep(.cm-string) {
  color: #98c379;
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