<template>
  <div v-if="showViewProperties" class="property-view">
    <!-- View Name Section -->
    <label>{{ isWorldView ? 'View' : 'Encounter' }} Name</label>
    <input
      id="encounterName"
      type="text"
      v-model="localName"
      :readonly="isWorldView"
      :class="{ 'readonly-name': isWorldView }"
      @input="!isWorldView && debouncedSaveName()"
      placeholder="Enter encounter name..."
    />

    <!-- Description Section -->
    <label>Description</label>
    <textarea
      v-model="localDescription"
      placeholder="Describe what this view represents..."
      rows="4"
      @input="saveDescription"
    />
    
    <!-- Todo List Section -->
    <label>Todo List</label>
    
    <!-- Add new todo -->
    <div class="todo-input-container">
      <input
        v-model="newTodoText"
        type="text"
        placeholder="Add a new todo item..."
        @keyup.enter="addTodo"
      />
      <button 
        class="todo-add-btn"
        :disabled="!newTodoText.trim()"
        @click="addTodo"
      >
        <v-icon size="small">mdi-plus</v-icon>
      </button>
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
        <button class="todo-edit-btn" @click="openEditDialog(todo)">✎</button>
        <button class="todo-delete-btn" @click="removeTodo(todo)">X</button>
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
        <button class="todo-edit-btn" @click="openEditDialog(todo)">✎</button>
        <button class="todo-delete-btn" @click="removeTodo(todo)">X</button>
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
import { MessageTypes } from '../../public/shared/SharedConstants.js';
import TodoEditDialog from '../components/TodoEditDialog.vue';

export default {
  name: 'EncounterPropertyView',
  
  components: {
    TodoEditDialog
  },
  
  props: {
    draw2dFrame: {
      type: Object,
      default: null
    }
  },
  
  data() {
    return {
      newTodoText: '',
      localName: '',
      localDescription: '',
      jsonData: null,  // Track selected element data (null = nothing selected)
      saveNameTimeout: null,  // Debounce timer for name saving
      showEditDialog: false,
      editingTodo: null
    };
  },
  
  computed: {
    ...mapGetters('views', ['currentView']),
    
    /**
     * Show view properties when:
     * - A view is loaded (currentView exists)
     * - Nothing is selected on the canvas (jsonData is null/empty)
     */
    showViewProperties() {
      return this.currentView && !this.jsonData;
    },
    
    /**
     * Check if current view is the world view (readonly name)
     */
    isWorldView() {
      const viewId = this.currentView?.viewId || this.currentView?.id;
      return viewId === 'world';
    },
    
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
  
  watch: {
    currentView: {
      immediate: true,
      handler(newView) {
        if (newView?.encounterConfig?.name !== undefined) {
          this.localName = newView.encounterConfig.name;
        } else {
          // Default name based on view type
          const viewId = newView?.viewId || newView?.id;
          this.localName = viewId === 'world' ? 'World' : '';
        }
        if (newView?.encounterConfig?.description !== undefined) {
          this.localDescription = newView.encounterConfig.description;
        } else {
          this.localDescription = '';
        }
      }
    }
  },
  
  methods: {
    /**
     * Debounced save name - waits 50ms after user stops typing
     */
    debouncedSaveName() {
      if (this.saveNameTimeout) {
        clearTimeout(this.saveNameTimeout);
      }
      this.saveNameTimeout = setTimeout(() => {
        this.saveName();
      }, 50);
    },
    
    /**
     * Save name - triggers full rename including file rename and navigation update
     */
    async saveName() {
      const trimmedName = this.localName.trim();
      const originalName = this.currentView?.encounterConfig?.name || '';
      
      // Only rename if name actually changed
      if (!trimmedName || trimmedName === originalName) {
        // Reset to original name if empty
        if (!trimmedName) {
          this.localName = originalName;
        }
        return;
      }
      
      try {
        const viewId = this.currentView.viewId || this.currentView.id;
        const gameName = this.$route.params.gameName;
        
        // Call renameView action which handles file rename
        const newViewId = await this.$store.dispatch('views/renameView', {
          gameName,
          viewId,
          newName: trimmedName
        });
        
        // Refresh encounters to update navigation
        await this.$store.dispatch('encounters/fetchEncounters', gameName);
        
        // Navigate to new URL if viewId changed
        if (newViewId && newViewId !== viewId) {
          const newEncounterId = newViewId.replace('encounter_', '');
          this.$router.replace(`/game/${gameName}/encounter/${newEncounterId}`);
        }
      } catch (error) {
        console.error('Failed to rename encounter:', error);
        // Reset to original name on error
        this.localName = originalName;
      }
    },
    
    /**
     * Save description to store
     */
    saveDescription() {
      this.updateEncounterConfig({ description: this.localDescription });
    },
    
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
      
      // Ensure all existing todos have IDs, then add the new one
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
     * Uses index for legacy todos without ID.
     */
    toggleTodo(todo) {
      const todoIndex = this.todos.findIndex((t, i) => 
        t.id ? t.id === todo.id : i === this.todos.indexOf(todo)
      );
      if (todoIndex === -1) return;
      
      // Ensure all todos have IDs when saving
      const todosWithIds = this.ensureTodoIds(this.todos);
      todosWithIds[todoIndex] = { ...todosWithIds[todoIndex], done: !todosWithIds[todoIndex].done };
      this.updateEncounterConfig({ todos: todosWithIds });
    },
    
    /**
     * Remove a todo item.
     * Uses index for legacy todos without ID.
     */
    removeTodo(todo) {
      const todoIndex = this.todos.findIndex((t, i) => 
        t.id ? t.id === todo.id : i === this.todos.indexOf(todo)
      );
      if (todoIndex === -1) return;
      
      // Ensure all todos have IDs when saving
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
      // Ensure all todos have IDs first
      const todosWithIds = this.ensureTodoIds(this.todos);
      
      // Find by ID (all todos now have IDs after ensureTodoIds)
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
    },
    
    /**
     * Handle canvas selection messages
     * Note: message.event contains the event type (C2V_SELECT, C2V_UNSELECT)
     *       message.type contains the shape type when applicable
     */
    handleMessage(event) {
      if (event.origin !== window.location.origin) return;
      
      const message = event.data;
      
      // Check message.event (not message.type) for the event type
      if (message.event === MessageTypes.C2V_SELECT) {
        this.jsonData = message.data;
      } else if (message.event === MessageTypes.C2V_UNSELECT) {
        this.jsonData = null;
      }
    }
  },
  
  mounted() {
    window.addEventListener('message', this.handleMessage);
  },
  
  beforeUnmount() {
    window.removeEventListener('message', this.handleMessage);
    if (this.saveNameTimeout) {
      clearTimeout(this.saveNameTimeout);
    }
  }
};
</script>

<style scoped>
.property-view {
  background: var(--game-bg-primary);
  color: var(--game-text-primary);
  height: 100%;
  overflow: auto;
  padding: var(--game-spacing-lg);
  box-sizing: border-box; 
  display: flex;
  flex-direction: column;
  gap: var(--game-spacing-md);
  font-size: var(--game-font-size-sm);
  border-left: 1px solid var(--game-border-color);
}

.property-view label {
  display: block;
  margin: 0 0 var(--game-spacing-xs) 0;
  font-size: var(--game-font-size-xs);
  color: var(--game-accent-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 600;
}

.property-view textarea,
.property-view input[type="text"] {
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

.property-view textarea:hover,
.property-view input[type="text"]:hover {
  background: var(--game-input-hover);
  border-color: var(--game-border-highlight);
}

.property-view textarea:focus,
.property-view input[type="text"]:focus {
  border-color: var(--game-input-focus);
  box-shadow: 0 0 0 2px rgba(233, 69, 96, 0.2);
}

/* Encounter Name - Special styling like stateName */
.property-view input#encounterName {
  font-family: var(--game-font-family-retro);
  font-size: 18px;
  letter-spacing: 2px;
  color: var(--game-accent-secondary);
  text-shadow: 2px 2px 0px rgba(0, 0, 0, 0.5);
  padding: var(--game-spacing-md) var(--game-spacing-lg);
}

/* Readonly name style for World view */
.property-view input#encounterName.readonly-name {
  background: transparent;
  border-color: transparent;
  cursor: default;
  pointer-events: none;
}

.property-view input#encounterName.readonly-name:hover,
.property-view input#encounterName.readonly-name:focus {
  background: transparent;
  border-color: transparent;
  box-shadow: none;
}

/* Todo Input Container */
.todo-input-container {
  display: flex;
  gap: var(--game-spacing-sm);
}

.todo-input-container input {
  flex: 1;
}

.todo-add-btn {
  background: var(--game-accent-primary);
  color: var(--game-text-primary);
  border: none;
  padding: var(--game-spacing-sm) var(--game-spacing-md);
  cursor: pointer;
  transition: all var(--game-transition-fast);
  display: flex;
  align-items: center;
  justify-content: center;
}

.todo-add-btn:hover:not(:disabled) {
  background: var(--game-accent-secondary);
}

.todo-add-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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
  font-size: var(--game-font-size-xs) !important;
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
  font-size: var(--game-font-size-sm);
  color: var(--game-text-primary);
}

.todo-item.completed .todo-text {
  text-decoration: line-through;
  color: var(--game-text-muted);
}

/* 8-bit Edit Button */
.todo-edit-btn {
  background: #4a9f4a;
  color: white;
  border: none;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-family: var(--game-font-family-retro);
  font-size: 12px;
  font-weight: bold;
  transition: all var(--game-transition-fast);
  opacity: 0;
  box-shadow: inset -2px -2px 0px 0px #2d6a2d;
  flex-shrink: 0;
}

.todo-item:hover .todo-edit-btn {
  opacity: 1;
}

.todo-edit-btn:hover {
  background: #5cb85c;
  box-shadow: inset -3px -3px 0px 0px #2d6a2d;
}

.todo-edit-btn:active {
  box-shadow: inset 2px 2px 0px 0px rgba(0, 0, 0, 0.4);
}

/* 8-bit Delete Button */
.todo-delete-btn {
  background: var(--game-accent-primary);
  color: white;
  border: none;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-family: var(--game-font-family-retro);
  font-size: 10px;
  font-weight: bold;
  transition: all var(--game-transition-fast);
  opacity: 0;
  box-shadow: inset -2px -2px 0px 0px #8c2022;
  flex-shrink: 0;
}

.todo-item:hover .todo-delete-btn {
  opacity: 1;
}

.todo-delete-btn:hover {
  background: #ce372b;
  box-shadow: inset -3px -3px 0px 0px #8c2022;
}

.todo-delete-btn:active {
  box-shadow: inset 2px 2px 0px 0px #8c2022;
}

/* Empty State */
.empty-state {
  text-align: center;
  color: var(--game-text-muted);
  font-size: var(--game-font-size-sm);
  padding: var(--game-spacing-lg);
  font-style: italic;
}
</style>