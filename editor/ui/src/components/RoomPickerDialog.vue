<template>
  <v-dialog v-model="dialogVisible" max-width="500" @update:model-value="onDialogChange">
    <v-card>
      <DialogHeader
        title="Test Game"
        subtitle="Select a room to start testing from."
        @close="close"
      />

      <div class="search-bar">
        <v-text-field
          ref="searchField"
          v-model="searchQuery"
          prepend-inner-icon="mdi-magnify"
          placeholder="Search rooms..."
          density="compact"
          hide-details
          clearable
          variant="outlined"
          @keydown.enter="confirmSelection"
          @keydown.down.prevent="moveSelection(1)"
          @keydown.up.prevent="moveSelection(-1)"
          @click:clear="searchQuery = ''"
        />
      </div>

      <v-card-text class="picker-content">
        <div v-if="filteredRooms.length === 0" class="empty-state">
          <v-icon size="36" class="mb-2">mdi-map-search</v-icon>
          <span>No rooms found</span>
        </div>
        <div v-else class="room-list">
          <div
            v-for="(room, index) in filteredRooms"
            :key="room.id"
            :class="['room-item', { 'room-item--selected': index === selectedIndex, 'room-item--start': room.isStart }]"
            @click="selectAndConfirm(room)"
            @mouseenter="selectedIndex = index"
          >
            <span class="room-item__name">{{ room.name }}</span>
            <span v-if="room.isStart" class="room-item__badge">START</span>
          </div>
        </div>
      </v-card-text>

      <v-card-actions class="dialog-actions">
        <v-spacer />
        <ThemedButton @click="close" variant="secondary">Cancel</ThemedButton>
        <ThemedButton @click="confirmSelection" :disabled="selectedIndex < 0">Start Test</ThemedButton>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import { mapGetters } from 'vuex'
import DialogHeader from './DialogHeader.vue'
import ThemedButton from './ThemedButton.vue'

export default {
  name: 'RoomPickerDialog',
  components: { DialogHeader, ThemedButton },
  props: {
    modelValue: { type: Boolean, default: false },
    preselectedRoom: { type: String, default: null }
  },
  emits: ['update:modelValue', 'select'],
  data() {
    return {
      searchQuery: '',
      selectedIndex: 0
    }
  },
  computed: {
    ...mapGetters('model', ['allStates']),
    dialogVisible: {
      get() { return this.modelValue },
      set(v) { this.$emit('update:modelValue', v) }
    },
    filteredRooms() {
      const rooms = [...(this.allStates || [])]
        .filter(s => s && s.name)
        .sort((a, b) => {
          if (a.stateType === 'START') return -1
          if (b.stateType === 'START') return 1
          return a.name.localeCompare(b.name)
        })
        .map(s => ({ id: s.id, name: s.name, isStart: s.stateType === 'START' }))

      if (!this.searchQuery) return rooms
      const q = this.searchQuery.toLowerCase()
      return rooms.filter(r => r.name.toLowerCase().includes(q))
    }
  },
  watch: {
    modelValue(val) {
      if (val) {
        this.searchQuery = ''
        this.$nextTick(() => {
          // Preselect the room that was active in the canvas
          const idx = this.filteredRooms.findIndex(r => r.name === this.preselectedRoom)
          this.selectedIndex = idx >= 0 ? idx : 0
          this.$refs.searchField?.focus()
        })
      }
    },
    searchQuery() {
      this.selectedIndex = 0
    }
  },
  methods: {
    moveSelection(delta) {
      const max = this.filteredRooms.length - 1
      this.selectedIndex = Math.max(0, Math.min(max, this.selectedIndex + delta))
    },
    confirmSelection() {
      const room = this.filteredRooms[this.selectedIndex]
      if (room) this.selectAndConfirm(room)
    },
    selectAndConfirm(room) {
      this.$emit('select', room.name)
      this.close()
    },
    close() {
      this.dialogVisible = false
    },
    onDialogChange(val) {
      if (!val) this.searchQuery = ''
    }
  }
}
</script>

<style scoped>
.search-bar {
  padding: 8px 16px 0;
}
.picker-content {
  padding: 8px 0 0 !important;
  max-height: 360px;
  overflow-y: auto;
}
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 32px;
  opacity: 0.5;
}
.room-list {
  display: flex;
  flex-direction: column;
}
.room-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  cursor: pointer;
  transition: background 0.1s;
}
.room-item--selected {
  background: rgba(127, 127, 127, 0.15);
}
.room-item__name {
  font-weight: 500;
  font-size: 0.9rem;
}
.room-item__badge {
  font-size: 0.65rem;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 3px;
  background: #d4af37;
  color: #1a1a1a;
  letter-spacing: 0.05em;
}
</style>
