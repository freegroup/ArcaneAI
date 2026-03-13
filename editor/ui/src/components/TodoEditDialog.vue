<template>
  <v-dialog v-model="dialogVisible" max-width="400" persistent>
    <v-card class="todo-edit-dialog">
      <DialogHeader
        title="Edit Todo"
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
        <ThemedButton variant="secondary" @click="cancel">Cancel</ThemedButton>
        <ThemedButton variant="primary" @click="save" :disabled="!localText.trim()">Save</ThemedButton>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import DialogHeader from './DialogHeader.vue';
import ThemedButton from './ThemedButton.vue';

export default {
  name: 'TodoEditDialog',
  
  components: {
    DialogHeader,
    ThemedButton
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
.todo-edit-content label {
  display: block;
}

.todo-edit-content textarea {
  width: 100%;
  outline: none;
  resize: vertical;
}

.todo-edit-actions {
  display: flex;
  justify-content: flex-end;
}
</style>