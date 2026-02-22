<template>
  <v-dialog v-model="dialogVisible" max-width="900" @update:model-value="onDialogChange">
    <v-card class="sound-picker-dialog">
      <DialogHeader 
        title="Select Sound" 
        icon="mdi-music-box"
        @close="close" 
      />

      <!-- Search Bar -->
      <div class="search-bar">
        <v-text-field
          v-model="searchQuery"
          prepend-inner-icon="mdi-magnify"
          placeholder="Search..."
          density="compact"
          hide-details
          clearable
          variant="outlined"
          @click:clear="searchQuery = ''"
        ></v-text-field>
      </div>

      <v-card-text class="dialog-content">
        <!-- Search Results (flat list) -->
        <div v-if="searchQuery && searchQuery.length > 0" class="search-results">
          <div class="search-results-header">
            {{ filteredFiles.length }} results for "{{ searchQuery }}"
          </div>
          <div class="search-results-list">
            <div
              v-for="file in filteredFiles"
              :key="file"
              class="search-result-item"
            >
              <v-btn
                icon
                size="x-small"
                variant="text"
                @click.stop="togglePlay(file)"
                class="play-btn"
              >
                <v-icon size="small">{{ playingFile === file ? 'mdi-stop' : 'mdi-play' }}</v-icon>
              </v-btn>
              <span class="file-name" @click="selectFile(file)">{{ file }}</span>
            </div>
          </div>
        </div>

        <!-- Finder-Style Column View -->
        <div v-else class="finder-columns" ref="finderColumns">
          <!-- Root Column (always visible) -->
          <div class="column">
            <div
              v-for="item in rootItems"
              :key="item.name"
              class="column-item"
              :class="{ selected: selectedPath[0] === item.name }"
              @click="selectItem(0, item)"
            >
              <v-icon v-if="item.type === 'clear'" size="small" class="clear-icon">mdi-volume-off</v-icon>
              <v-icon v-else-if="item.type === 'folder'" size="small" class="folder-icon">{{ selectedPath[0] === item.name ? 'mdi-folder-open' : 'mdi-folder' }}</v-icon>
              <span class="item-name">{{ item.name }}</span>
              <v-icon v-if="item.type === 'folder'" size="small" class="folder-arrow">mdi-chevron-right</v-icon>
            </div>
          </div>

          <!-- Dynamic Columns based on selectedPath -->
          <div
            v-for="(segment, depth) in selectedPath"
            :key="depth"
            class="column"
          >
            <div
              v-for="item in getItemsAtDepth(depth + 1)"
              :key="item.name"
              class="column-item"
              :class="{ selected: selectedPath[depth + 1] === item.name }"
              @click="selectItem(depth + 1, item)"
            >
              <template v-if="item.type === 'file'">
                <v-btn
                  icon
                  size="x-small"
                  variant="text"
                  @click.stop="togglePlay(item.fullPath)"
                  class="play-btn"
                >
                  <v-icon size="small">{{ playingFile === item.fullPath ? 'mdi-stop' : 'mdi-play' }}</v-icon>
                </v-btn>
                <span class="item-name file-item" @click.stop="selectFile(item.fullPath)">{{ item.name }}</span>
              </template>
              <template v-else>
                <span class="item-name">{{ item.name }}</span>
                <v-icon size="small" class="folder-arrow">mdi-chevron-right</v-icon>
              </template>
            </div>
          </div>
        </div>
      </v-card-text>

      <!-- Selected File Display -->
      <div v-if="selectedFile" class="selected-display">
        <v-icon size="small" class="mr-2">mdi-music-note</v-icon>
        {{ selectedFile }}
      </div>

      <v-card-actions class="dialog-actions">
        <v-spacer></v-spacer>
        <v-btn class="btn-8bit btn-secondary" @click="close">Cancel</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import SoundManager from '@/utils/SoundManager';
import DialogHeader from './DialogHeader.vue';

export default {
  name: 'SoundSelectDialog',
  
  props: {
    modelValue: {
      type: Boolean,
      default: false
    },
    files: {
      type: Array,
      default: () => []
    },
    currentValue: {
      type: String,
      default: ''
    }
  },

  components: { DialogHeader },
  emits: ['update:modelValue', 'select'],

  data() {
    return {
      searchQuery: '',
      selectedPath: [],
      selectedFile: null,
      playingFile: null,
      soundListener: null
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
    },

    // Build tree structure from flat file list
    fileTree() {
      const tree = {};
      
      for (const filePath of this.files) {
        const parts = filePath.split('/');
        let current = tree;
        
        for (let i = 0; i < parts.length; i++) {
          const part = parts[i];
          const isFile = i === parts.length - 1;
          
          if (!current[part]) {
            current[part] = {
              name: part,
              type: isFile ? 'file' : 'folder',
              fullPath: isFile ? filePath : null,
              children: isFile ? null : {}
            };
          }
          
          if (!isFile) {
            current = current[part].children;
          }
        }
      }
      
      return tree;
    },

    // Root level items (with "No Sound" option first)
    rootItems() {
      const noSoundOption = {
        name: 'Use No Sound',
        type: 'clear',
        fullPath: null
      };
      return [noSoundOption, ...this.getSortedItems(this.fileTree)];
    },

    // Search filtered files
    filteredFiles() {
      if (!this.searchQuery) return [];
      const query = this.searchQuery.toLowerCase();
      return this.files.filter(file => file.toLowerCase().includes(query));
    }
  },

  watch: {
    modelValue(newVal) {
      if (newVal) {
        // Dialog opened - reset state
        this.searchQuery = '';
        this.selectedPath = [];
        this.selectedFile = this.currentValue || null;
        
        // If current value exists, expand to it
        if (this.currentValue) {
          this.expandToFile(this.currentValue);
        }
      } else {
        // Dialog closed - stop any playing sound
        this.stopSound();
      }
    }
  },

  mounted() {
    // Listen to SoundManager events
    this.soundListener = SoundManager.addListener((isPlaying) => {
      if (!isPlaying) {
        this.playingFile = null;
      }
    });
  },

  beforeUnmount() {
    if (this.soundListener) {
      this.soundListener();
      this.soundListener = null;
    }
    this.stopSound();
  },

  methods: {
    // Get sorted items from a tree node (folders first, then files, alphabetically)
    getSortedItems(node) {
      if (!node) return [];
      
      const items = Object.values(node);
      const folders = items.filter(item => item.type === 'folder').sort((a, b) => a.name.localeCompare(b.name));
      const files = items.filter(item => item.type === 'file').sort((a, b) => a.name.localeCompare(b.name));
      
      return [...folders, ...files];
    },

    // Get items at a specific depth based on selectedPath
    getItemsAtDepth(depth) {
      let current = this.fileTree;
      
      for (let i = 0; i < depth; i++) {
        const segment = this.selectedPath[i];
        if (!segment || !current[segment]) return [];
        current = current[segment].children;
      }
      
      return this.getSortedItems(current);
    },

    // Handle item selection
    selectItem(depth, item) {
      if (item.type === 'clear') {
        // "No Sound" option selected - clear the sound
        this.clearSound();
      } else if (item.type === 'folder') {
        // Truncate path and add new segment
        this.selectedPath = [...this.selectedPath.slice(0, depth), item.name];
        this.selectedFile = null;
        
        // Scroll to show new column
        this.$nextTick(() => {
          if (this.$refs.finderColumns) {
            this.$refs.finderColumns.scrollLeft = this.$refs.finderColumns.scrollWidth;
          }
        });
      } else {
        // File selected - set as selected
        this.selectFile(item.fullPath);
      }
    },

    // Clear sound selection
    clearSound() {
      this.stopSound();
      this.selectedFile = null;
      this.$emit('select', '');
      this.close();
    },

    // Select a file
    selectFile(filePath) {
      this.selectedFile = filePath;
      this.confirm();
    },

    // Expand tree to show a specific file
    expandToFile(filePath) {
      const parts = filePath.split('/');
      // Remove the file name, keep only directories
      this.selectedPath = parts.slice(0, -1);
    },

    // Toggle sound playback
    togglePlay(filePath) {
      if (this.playingFile === filePath) {
        this.stopSound();
      } else {
        this.playSound(filePath);
      }
    },

    // Play a sound
    playSound(filePath) {
      this.playingFile = filePath;
      SoundManager.playSound(filePath, 100);
    },

    // Stop current sound
    stopSound() {
      SoundManager.stopCurrentSound();
      this.playingFile = null;
    },

    // Confirm selection
    confirm() {
      if (this.selectedFile) {
        this.$emit('select', this.selectedFile);
        this.close();
      }
    },

    // Close dialog
    close() {
      this.stopSound();
      this.dialogVisible = false;
    },

    // Handle dialog visibility change
    onDialogChange(value) {
      if (!value) {
        this.stopSound();
      }
    }
  }
};
</script>

<style scoped>
.sound-picker-dialog {
  background: var(--game-bg-primary);
  color: var(--game-text-primary);
}


.search-bar {
  padding: 12px 16px;
  border-bottom: 1px solid var(--game-border-color);
}

.dialog-content {
  padding: 0 !important;
  height: 400px;
  overflow: hidden;
}

/* Finder Column View */
.finder-columns {
  display: flex;
  height: 100%;
  overflow-x: auto;
  overflow-y: hidden;
}

.column {
  min-width: 150px;
  width: 200px;
  max-width: 400px;
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
  border-right: 3px solid var(--game-accent-primary);
  flex-shrink: 0;
  resize: horizontal;
  position: relative;
}

.column:last-child {
  border-right: none;
  /* Last column (file column) can be wider */
  width: 250px;
  max-width: 500px;
}

/* Red resize border indicator */
.column:not(:last-child):hover {
  border-right-color: var(--game-accent-tertiary);
}

/* Resize handle - limited styling support but try */
.column::-webkit-resizer {
  background: var(--game-accent-primary);
}

.column-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  cursor: pointer;
  transition: background-color 0.15s;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.column-item:hover {
  background: var(--game-input-hover);
}

.column-item.selected {
  background: var(--game-accent-primary);
  color: var(--game-text-primary);
}

.item-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
  font-family: var(--game-font-family-retro);
  letter-spacing: 0.5px;
}

.file-item {
  cursor: pointer;
}

.file-item:hover {
  text-decoration: underline;
}

.clear-icon,
.folder-icon {
  margin-right: 12px;
  color: var(--game-accent-secondary);
}

.column-item.selected .clear-icon,
.column-item.selected .folder-icon {
  color: var(--game-text-primary);
}

.folder-arrow {
  opacity: 0.6;
  margin-left: 4px;
}

.play-btn {
  margin-right: 8px;
  color: var(--game-accent-secondary) !important;
}

.play-btn:hover {
  color: var(--game-accent-primary) !important;
}

/* Search Results View */
.search-results {
  height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.search-results-header {
  padding: 12px 16px;
  font-size: 12px;
  color: var(--game-text-secondary);
  border-bottom: 1px solid var(--game-border-color);
  flex-shrink: 0;
}

.search-results-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.search-result-item {
  display: flex;
  align-items: center;
  padding: 6px 16px;
  cursor: pointer;
  transition: background-color 0.15s;
}

.search-result-item:hover {
  background: var(--game-input-hover);
}

.search-result-item .file-name {
  flex: 1;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.search-result-item .file-name:hover {
  text-decoration: underline;
}

/* Selected Display */
.selected-display {
  display: flex;
  align-items: center;
  padding: 8px 16px;
  background: var(--game-bg-secondary);
  border-top: 1px solid var(--game-border-color);
  font-size: 12px;
  color: var(--game-text-secondary);
}

/* Dialog Actions */
.dialog-actions {
  border-top: 1px solid var(--game-border-color);
  padding: 12px 16px;
  gap: 12px;
}

/* 8-bit Style Buttons */
.btn-8bit {
  font-family: var(--game-font-family-retro) !important;
  font-size: 12px !important;
  letter-spacing: 1px !important;
  text-transform: uppercase !important;
  border-radius: 0 !important;
  padding: 8px 20px !important;
  min-width: 100px !important;
  height: 36px !important;
  transition: all var(--game-transition-fast) !important;
}

.btn-8bit.btn-primary {
  background: var(--game-accent-primary) !important;
  color: var(--game-text-primary) !important;
  box-shadow: inset -4px -4px 0px 0px #8c2022,
              0 0 0 3px black !important;
}

.btn-8bit.btn-primary:hover:not(:disabled) {
  background: var(--game-accent-tertiary) !important;
  box-shadow: inset -6px -6px 0px 0px #8c2022,
              0 0 0 3px black !important;
}

.btn-8bit.btn-primary:active:not(:disabled) {
  box-shadow: inset 4px 4px 0px 0px #8c2022,
              0 0 0 3px black !important;
}

.btn-8bit.btn-primary:disabled {
  background: var(--game-text-muted) !important;
  box-shadow: inset -4px -4px 0px 0px #555,
              0 0 0 3px #555 !important;
  opacity: 0.5 !important;
  cursor: not-allowed !important;
}

.btn-8bit.btn-secondary {
  background: var(--game-bg-secondary) !important;
  color: var(--game-text-primary) !important;
  box-shadow: inset -4px -4px 0px 0px #333,
              0 0 0 3px var(--game-border-color) !important;
}

.btn-8bit.btn-secondary:hover {
  background: var(--game-input-hover) !important;
  box-shadow: inset -6px -6px 0px 0px #333,
              0 0 0 3px var(--game-border-highlight) !important;
}

.btn-8bit.btn-secondary:active {
  box-shadow: inset 4px 4px 0px 0px #333,
              0 0 0 3px var(--game-border-color) !important;
}

/* Scrollbar styling */
.column::-webkit-scrollbar,
.search-results-list::-webkit-scrollbar,
.finder-columns::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.column::-webkit-scrollbar-track,
.search-results-list::-webkit-scrollbar-track,
.finder-columns::-webkit-scrollbar-track {
  background: var(--game-bg-primary);
}

.column::-webkit-scrollbar-thumb,
.search-results-list::-webkit-scrollbar-thumb,
.finder-columns::-webkit-scrollbar-thumb {
  background: var(--game-border-color);
  border-radius: 4px;
}

.column::-webkit-scrollbar-thumb:hover,
.search-results-list::-webkit-scrollbar-thumb:hover,
.finder-columns::-webkit-scrollbar-thumb:hover {
  background: var(--game-text-muted);
}
</style>