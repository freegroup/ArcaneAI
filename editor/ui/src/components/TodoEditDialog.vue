<template>
  <v-dialog v-model="dialogVisible" max-width="400" persistent>
    <v-card class="todo-edit-dialog">
      <DialogHeader 
        title="Edit Todo" 
        icon="mdi-pencil"
        @close="cancel"
      />
      
      <v-card-text class="todo-edit-content">
        <label>Todo Text</label>
        <textarea
          ref="todoInput"
          v-model="localText"
          placeholder="Enter todo text..."
          rows="3"
          @keyup.enter.ctrl="save"
        />
      </v-card-text>
      
      <v-card-actions class="todo-edit-actions">
        <RetroButton variant="secondary" @click="cancel">Cancel</RetroButton>
        <RetroButton variant="primary" @click="save" :disabled="!localText.trim()">Save</RetroButton>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import DialogHeader from './DialogHeader.vue';
import RetroButton from './RetroButton.vue';

export default {
  name: 'TodoEditDialog',
  
  components: {
    DialogHeader,
    RetroButton
  },
  
  props: {
    modelValue: {
      type: Boolean,
      default: false
    },
    todo: {
      type: Object,
      default: null
    }
  },
  
  emits: ['update:modelValue', 'save'],
  
  data() {
    return {
      localText: ''
    };
  },
  
  computed: {
    dialogVisible: {
      get() {
        return this.modelValue;
      },
      set(value) {
        this.$emit('update:modelValue', value);
      }
    }
  },
  
  watch: {
    modelValue(isOpen) {
      if (isOpen && this.todo) {
        this.localText = this.todo.text || '';
        this.$nextTick(() => {
          this.$refs.todoInput?.focus();
          this.$refs.todoInput?.select();
        });
      }
    }
  },
  
  methods: {
    save() {
      if (!this.localText.trim()) return;
      
      this.$emit('save', {
        ...this.todo,
        text: this.localText.trim()
      });
      this.dialogVisible = false;
    },
    
    cancel() {
      this.dialogVisible = false;
    }
  }
};
</script>

<style scoped>
.todo-edit-dialog {
  background: var(--game-bg-secondary) !important;
  border: 3px solid var(--game-accent-primary);
  border-radius: 0 !important;
}

.todo-edit-content {
  padding: var(--game-spacing-lg) !important;
}

.todo-edit-content label {
  display: block;
  margin: 0 0 var(--game-spacing-xs) 0;
  font-size: var(--game-font-size-md);
  color: var(--game-accent-secondary);
  text-transform: uppercase;
  letter-spacing: 4px;
}

.todo-edit-content textarea {
  width: 100%;
  padding: var(--game-spacing-sm) var(--game-spacing-md);
  background: var(--game-input-bg);
  border: 1px solid var(--game-input-border);
  border-radius: 0;
  color: var(--game-text-primary);
  font-size: var(--game-font-size-md);
  font-family: inherit;
  transition: all var(--game-transition-fast);
  outline: none;
  resize: vertical;
}

.todo-edit-content textarea:focus {
  border-color: var(--game-input-focus);
  box-shadow: 0 0 0 2px rgba(233, 69, 96, 0.2);
}

.todo-edit-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--game-spacing-md);
  padding: var(--game-spacing-md) var(--game-spacing-lg) var(--game-spacing-lg) !important;
  background: var(--game-bg-tertiary);
  border-top: 1px solid var(--game-border-color);
}
</style>