<template>
  <div class="todo-manager">
    <label>Todo List</label>
    
    <!-- Add new todo -->
    <div class="todo-input-container">
      <input
        v-model="newTodoText"
        type="text"
        placeholder="Add a new todo item..."
        @keyup.enter="addTodo"
      />
      <RetroActionButton
        variant="success"
        :disabled="!newTodoText.trim()"
        @click="addTodo"
        title="Add todo"
      >
        <v-icon size="small">mdi-plus</v-icon>
      </RetroActionButton>
    </div>
    
    <!-- Pending todos -->
    <div v-if="pendingTodos.length > 0" class="todo-section">
      <div 
        v-for="todo in pendingTodos" 
        :key="todo.id || todo.text"
        class="todo-item"
      >
        <input
          type="checkbox"
          :checked="todo.done"
          @change="toggleTodo(todo)"
          class="todo-checkbox"
        />
        <span class="todo-text">{{ todo.text }}</span>
        <RetroActionButton variant="secondary" @click="openEditDialog(todo)" class="todo-action-btn">✎</RetroActionButton>
        <RetroActionButton variant="danger" @click="removeTodo(todo)" class="todo-action-btn">X</RetroActionButton>
      </div>
    </div>
    
    <!-- Completed todos -->
    <div v-if="completedTodos.length > 0" class="todo-section completed-section">
      <label class="section-label">Completed</label>
      <div 
        v-for="todo in completedTodos" 
        :key="todo.id || todo.text"
        class="todo-item completed"
      >
        <input
          type="checkbox"
          :checked="todo.done"
          @change="toggleTodo(todo)"
          class="todo-checkbox"
        />
        <span class="todo-text">{{ todo.text }}</span>
        <RetroActionButton variant="secondary" @click="openEditDialog(todo)" class="todo-action-btn">✎</RetroActionButton>
        <RetroActionButton variant="danger" @click="removeTodo(todo)" class="todo-action-btn">X</RetroActionButton>
      </div>
    </div>
    
    <!-- Empty state -->
    <div v-if="todos.length === 0" class="empty-state">
      No todos yet. Add one above.
    </div>
    
    <!-- Edit Todo Dialog -->
    <TodoEditDialog
      v-model="showEditDialog"
      :todo="editingTodo"
      @save="saveTodoEdit"
    />
  </div>
</template>

<script>
import { mapGetters } from 'vuex';
import TodoEditDialog from './TodoEditDialog.vue';
import RetroActionButton from './RetroActionButton.vue';

export default {
  name: 'TodoManager',
  
  components: {
    TodoEditDialog,
    RetroActionButton
  },
  
  data() {
    return {
      newTodoText: '',
      showEditDialog: false,
      editingTodo: null
    };
  },
  
  computed: {
    ...mapGetters('views', ['currentView']),
    
    /**
     * Get todos from encounterConfig.
     */
    todos() {
      return this.currentView?.encounterConfig?.todos || [];
    },
    
    /**
     * Filter pending (not done) todos
     */
    pendingTodos() {
      return this.todos.filter(t => !t.done);
    },
    
    /**
     * Filter completed (done) todos
     */
    completedTodos() {
      return this.todos.filter(t => t.done);
    }
  },
  
  methods: {
    /**
     * Generate a unique ID for todos
     */
    generateTodoId() {
      return `todo_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    },
    
    /**
     * Migrate legacy todos to have unique IDs.
     * Returns a new array with all todos having IDs.
     */
    ensureTodoIds(todos) {
      return todos.map((todo) => {
        if (!todo.id) {
          return {
            ...todo,
            id: this.generateTodoId()
          };
        }
        return todo;
      });
    },
    
    /**
     * Add a new todo item
     */
    addTodo() {
      if (!this.newTodoText.trim()) return;
      
      const todosWithIds = this.ensureTodoIds(this.todos);
      const newTodos = [
        ...todosWithIds,
        { 
          id: this.generateTodoId(),
          text: this.newTodoText.trim(), 
          done: false 
        }
      ];
      
      this.updateEncounterConfig({ todos: newTodos });
      this.newTodoText = '';
    },
    
    /**
     * Toggle todo done state.
     */
    toggleTodo(todo) {
      const todoIndex = this.todos.findIndex((t, i) => 
        t.id ? t.id === todo.id : i === this.todos.indexOf(todo)
      );
      if (todoIndex === -1) return;
      
      const todosWithIds = this.ensureTodoIds(this.todos);
      todosWithIds[todoIndex] = { ...todosWithIds[todoIndex], done: !todosWithIds[todoIndex].done };
      this.updateEncounterConfig({ todos: todosWithIds });
    },
    
    /**
     * Remove a todo item.
     */
    removeTodo(todo) {
      const todoIndex = this.todos.findIndex((t, i) => 
        t.id ? t.id === todo.id : i === this.todos.indexOf(todo)
      );
      if (todoIndex === -1) return;
      
      const todosWithIds = this.ensureTodoIds(this.todos);
      todosWithIds.splice(todoIndex, 1);
      this.updateEncounterConfig({ todos: todosWithIds });
    },
    
    /**
     * Open edit dialog for a todo
     */
    openEditDialog(todo) {
      this.editingTodo = { ...todo };
      this.showEditDialog = true;
    },
    
    /**
     * Save edited todo
     */
    saveTodoEdit(updatedTodo) {
      const todosWithIds = this.ensureTodoIds(this.todos);
      
      const newTodos = todosWithIds.map(t => 
        t.id === updatedTodo.id ? { ...updatedTodo, id: t.id } : t
      );
      this.updateEncounterConfig({ todos: newTodos });
    },
    
    /**
     * Helper to update encounterConfig
     */
    updateEncounterConfig(updates) {
      if (!this.currentView) return;
      
      const currentConfig = this.currentView.encounterConfig || {};
      const newConfig = { ...currentConfig, ...updates };
      
      this.$store.commit('views/PATCH_ENCOUNTER_CONFIG', {
        viewId: this.currentView.viewId || this.currentView.id,
        encounterConfig: newConfig
      });
    }
  }
};
</script>

<style scoped>
.todo-manager {
  display: flex;
  flex-direction: column;
  gap: var(--game-spacing-sm);
}

label {
  display: block;
  margin: 0 0 var(--game-spacing-xs) 0;
  font-size: var(--game-font-size-md);
  color: var(--game-accent-secondary);
  text-transform: uppercase;
  letter-spacing: 2px;
}

/* Todo Input Container */
.todo-input-container {
  display: flex;
  gap: var(--game-spacing-sm);
}

.todo-input-container input {
  flex: 1;
  padding: var(--game-spacing-sm) var(--game-spacing-md);
  background: var(--game-input-bg);
  border: 1px solid var(--game-input-border);
  border-radius: 0;
  color: var(--game-text-primary);
  outline: none;
}

.todo-input-container input:focus {
  border-color: var(--game-input-focus);
}

.todo-input-container input:focus {
  border-color: var(--game-input-focus);
}

/* Todo Section */
.todo-section {
  border-left: 2px solid var(--game-border-color);
  padding-left: var(--game-spacing-md);
  margin-top: var(--game-spacing-sm);
}

.completed-section {
  margin-top: var(--game-spacing-lg);
}

.section-label {
  font-size: var(--game-font-size-md) !important;
  color: var(--game-text-muted) !important;
  margin-bottom: var(--game-spacing-sm) !important;
}

/* Todo Item */
.todo-item {
  display: flex;
  align-items: center;
  gap: var(--game-spacing-sm);
  padding: var(--game-spacing-xs) 0;
  transition: background var(--game-transition-fast);
}

.todo-item:hover {
  background: rgba(255, 255, 255, 0.03);
}

.todo-checkbox {
  width: 16px;
  height: 16px;
  accent-color: var(--game-accent-primary);
  cursor: pointer;
  flex-shrink: 0;
}

.todo-text {
  flex: 1;
  font-size: var(--game-font-size-md);
  color: var(--game-text-primary);
}

.todo-item.completed .todo-text {
  text-decoration: line-through;
  color: var(--game-text-muted);
}

/* 8-bit Action Buttons Visibility */
.todo-action-btn {
  opacity: 0;
  transition: opacity var(--game-transition-fast);
}

.todo-item:hover .todo-action-btn {
  opacity: 1;
}

.empty-state {
  text-align: center;
  color: var(--game-text-muted);
  font-size: var(--game-font-size-sm);
  padding: var(--game-spacing-lg);
}
</style>
