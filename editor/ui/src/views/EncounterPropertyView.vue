<template>
  <div v-if="showViewProperties" class="property-view">
    <!-- Encounter Name Section -->
    <label>Encounter Name</label>
    <input
      id="encounterName"
      type="text"
      v-model="localName"
      @input="debouncedSaveName"
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
        v-for="(todo, index) in pendingTodos" 
        :key="'pending-' + index"
        class="todo-item"
      >
        <input
          type="checkbox"
          :checked="todo.done"
          @change="toggleTodo(todo)"
          class="todo-checkbox"
        />
        <span class="todo-text">{{ todo.text }}</span>
        <button class="todo-delete-btn" @click="removeTodo(todo)">
          <v-icon size="x-small">mdi-delete-outline</v-icon>
        </button>
      </div>
    </div>
    
    <!-- Completed todos -->
    <div v-if="completedTodos.length > 0" class="todo-section completed-section">
      <label class="section-label">Completed</label>
      <div 
        v-for="(todo, index) in completedTodos" 
        :key="'completed-' + index"
        class="todo-item completed"
      >
        <input
          type="checkbox"
          :checked="todo.done"
          @change="toggleTodo(todo)"
          class="todo-checkbox"
        />
        <span class="todo-text">{{ todo.text }}</span>
        <button class="todo-delete-btn" @click="removeTodo(todo)">
          <v-icon size="x-small">mdi-delete-outline</v-icon>
        </button>
      </div>
    </div>
    
    <!-- Empty state -->
    <div v-if="todos.length === 0" class="empty-state">
      No todos yet. Add one above.
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex';
import { MessageTypes } from '../../public/shared/SharedConstants.js';

export default {
  name: 'EncounterPropertyView',
  
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
      saveNameTimeout: null  // Debounce timer for name saving
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
     * Get todos from encounterConfig
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
          this.localName = '';
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
     * Add a new todo item
     */
    addTodo() {
      if (!this.newTodoText.trim()) return;
      
      const newTodos = [
        ...this.todos,
        { text: this.newTodoText.trim(), done: false }
      ];
      
      this.updateEncounterConfig({ todos: newTodos });
      this.newTodoText = '';
    },
    
    /**
     * Toggle todo done state
     */
    toggleTodo(todo) {
      const newTodos = this.todos.map(t => 
        t === todo ? { ...t, done: !t.done } : t
      );
      this.updateEncounterConfig({ todos: newTodos });
    },
    
    /**
     * Remove a todo item
     */
    removeTodo(todo) {
      const newTodos = this.todos.filter(t => t !== todo);
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

.todo-delete-btn {
  background: transparent;
  border: none;
  color: var(--game-text-muted);
  cursor: pointer;
  padding: var(--game-spacing-xs);
  opacity: 0;
  transition: all var(--game-transition-fast);
  display: flex;
  align-items: center;
  justify-content: center;
}

.todo-item:hover .todo-delete-btn {
  opacity: 1;
}

.todo-delete-btn:hover {
  color: var(--game-accent-primary);
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