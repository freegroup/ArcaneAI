<template>
  <v-navigation-drawer
    location="right"
    permanent
    :width="collapsed ? 0 : sidebarWidth"
    class="room-sidebar"
  >
    <button
      class="sidebar-toggle"
      @click="collapsed = !collapsed"
      :title="collapsed ? 'Expand panel' : 'Collapse panel'"
    >
      {{ collapsed ? '◀' : '▶' }}
    </button>

    <div class="room-sidebar__content" v-show="!collapsed">

      <!-- Ambient Sound (same pattern as StateProperty.vue) -->
      <section class="room-sidebar__section">
        <h4 class="room-sidebar__title">Ambient Sound</h4>
        <div class="sound-selection">
          <div class="sound-display" @click="showSoundPicker = true">
            <v-icon size="small" class="sound-icon">mdi-music-note</v-icon>
            <span class="sound-name">{{ ambientSound || 'No sound selected' }}</span>
            <v-icon size="small" class="browse-icon">mdi-folder-open</v-icon>
          </div>
          <v-btn icon size="small" @click="toggleSound" :disabled="!ambientSound">
            <v-icon size="small">{{ isPlaying ? 'mdi-stop' : 'mdi-play' }}</v-icon>
          </v-btn>
        </div>

        <SoundSelectDialog
          v-model="showSoundPicker"
          :files="soundFiles"
          :currentValue="ambientSound"
          @select="onSoundSelected"
        />

        <v-slider
          v-if="ambientSound"
          :model-value="ambientVolume ?? 100"
          @update:model-value="onVolumeChange"
          :min="1"
          :max="100"
          :step="1"
          append-icon="mdi-volume-high"
          density="compact"
          hide-details
          class="room-sidebar__slider"
        />
      </section>

      <section class="room-sidebar__section">
        <h4 class="room-sidebar__title">Actions</h4>
        <p v-if="!triggers || triggers.length === 0" class="room-sidebar__muted">No actions.</p>
        <ul class="room-sidebar__list" v-else>
          <li v-for="t in triggers" :key="t.id || t.name" class="room-sidebar__item room-sidebar__item--action">
            <span class="room-sidebar__item-name">{{ t.name }}</span>
            <button
              class="room-sidebar__edit-btn"
              @click="editTrigger(t)"
              title="Edit action"
            >…</button>
          </li>
        </ul>
      </section>

      <section class="room-sidebar__section">
        <h4 class="room-sidebar__title">Exits</h4>
        <p v-if="!exits || exits.length === 0" class="room-sidebar__muted">No exits.</p>
        <ul class="room-sidebar__list" v-else>
          <li v-for="c in exits" :key="c.id" class="room-sidebar__item room-sidebar__item--action">
            <span class="room-sidebar__item-name">
              {{ c.name || '(unbenannt)' }}
              <span class="room-sidebar__arrow">→</span>
              <router-link
                v-if="c.targetName && gameName"
                :to="`/game/${gameName}/rooms/${c.targetName}`"
                class="room-sidebar__link"
                @click.stop
              >{{ c.targetName }}</router-link>
              <span v-else class="room-sidebar__muted">{{ c.targetId }}</span>
            </span>
            <button
              class="room-sidebar__edit-btn"
              @click="editExit(c)"
              title="Edit exit"
            >…</button>
          </li>
        </ul>
      </section>

    </div>

    <RoomActionEditor
      v-model="editorOpen"
      :trigger="editingTrigger"
    />
    <RoomExitEditor
      v-model="exitEditorOpen"
      :exit="editingExit"
      :source-id="sourceId"
    />
  </v-navigation-drawer>
</template>

<script>
import { mapGetters } from 'vuex'
import SoundManager from '@/utils/SoundManager'
import SoundSelectDialog from '@/components/SoundSelectDialog.vue'
import RoomActionEditor from './RoomActionEditor.vue'
import RoomExitEditor from './RoomExitEditor.vue'

export default {
  name: 'RoomSidebar',
  components: { SoundSelectDialog, RoomActionEditor, RoomExitEditor },
  props: {
    gameName: { type: String, default: '' },
    sourceId: { type: String, default: null },
    ambientSound: { type: String, default: null },
    ambientVolume: { type: Number, default: null },
    triggers: { type: Array, default: () => [] },
    exits: { type: Array, default: () => [] }
  },
  emits: ['update:ambient-sound', 'update:ambient-volume'],
  data() {
    return {
      collapsed: false,
      showSoundPicker: false,
      isPlaying: false,
      removeSoundListener: null,
      editorOpen: false,
      editingTrigger: null,
      exitEditorOpen: false,
      editingExit: null
    }
  },
  computed: {
    ...mapGetters('sounds', ['files']),
    soundFiles() {
      return this.files
    },
    sidebarWidth() {
      const w = this.$vuetify.display.width
      if (w < 1500) return Math.round(w / 4)
      return 360
    }
  },
  mounted() {
    this.removeSoundListener = SoundManager.addListener((isPlaying) => {
      this.isPlaying = isPlaying
    })
  },
  beforeUnmount() {
    if (typeof this.removeSoundListener === 'function') {
      this.removeSoundListener()
    }
    SoundManager.stopCurrentSound()
  },
  methods: {
    onSoundSelected(soundPath) {
      this.$emit('update:ambient-sound', soundPath)
    },
    onVolumeChange(value) {
      SoundManager.setVolume(value)
      this.$emit('update:ambient-volume', value)
    },
    toggleSound() {
      if (this.isPlaying) {
        SoundManager.stopCurrentSound()
      } else if (this.ambientSound) {
        const volume = this.ambientVolume ?? 100
        SoundManager.playSound(this.ambientSound, volume)
      }
    },
    editTrigger(t) {
      this.editingTrigger = t
      this.editorOpen = true
    },
    editExit(c) {
      this.editingExit = c
      this.exitEditorOpen = true
    }
  }
}
</script>

<style scoped>
.sidebar-toggle {
  position: absolute;
  top: 50%;
  left: -24px;
  transform: translateY(-50%);
  width: 24px;
  height: 48px;
  border: none;
  border-radius: 4px 0 0 4px;
  background: rgba(127, 127, 127, 0.15);
  cursor: pointer;
  z-index: 10;
}
.sidebar-toggle:hover {
  background: rgba(127, 127, 127, 0.3);
}

.room-sidebar__content {
  padding: 16px 18px;
  overflow-y: auto;
  height: 100%;
}
.room-sidebar__section {
  margin-bottom: 22px;
}
.room-sidebar__section:last-child {
  margin-bottom: 0;
}
.room-sidebar__title {
  margin: 0 0 8px 0;
  font-size: 0.78rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  opacity: 0.75;
}

/* Sound Picker — same pattern as StateProperty.vue */
.sound-selection {
  display: flex;
  align-items: center;
  gap: 6px;
}
.sound-display {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border: 1px solid rgba(127, 127, 127, 0.3);
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.15s;
}
.sound-display:hover {
  background: rgba(127, 127, 127, 0.08);
}
.sound-name {
  flex: 1;
  font-size: 0.85rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.sound-icon, .browse-icon {
  opacity: 0.6;
}
.room-sidebar__slider {
  margin-top: 8px;
}

.room-sidebar__muted {
  opacity: 0.6;
  font-size: 0.85rem;
}
.room-sidebar__list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.room-sidebar__item {
  padding: 8px 10px;
  margin-bottom: 6px;
  border: 1px solid rgba(127, 127, 127, 0.25);
  border-radius: 4px;
}
.room-sidebar__item-name {
  font-weight: 600;
  font-size: 0.88rem;
  margin-bottom: 3px;
}
.room-sidebar__item--action {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 10px;
}
.room-sidebar__item--action .room-sidebar__item-name {
  margin-bottom: 0;
}
.room-sidebar__edit-btn {
  background: none;
  border: 1px solid rgba(127, 127, 127, 0.3);
  border-radius: 4px;
  cursor: pointer;
  padding: 0 8px;
  height: 24px;
  font-size: 1rem;
  line-height: 1;
  color: inherit;
  opacity: 0.7;
  transition: opacity 0.15s, background 0.15s;
}
.room-sidebar__edit-btn:hover {
  opacity: 1;
  background: rgba(127, 127, 127, 0.12);
}
.room-sidebar__arrow {
  margin: 0 5px;
  opacity: 0.6;
}
.room-sidebar__link {
  color: inherit;
  text-decoration: underline;
  text-underline-offset: 3px;
}
.room-sidebar__item-desc {
  font-size: 0.82rem;
  opacity: 0.85;
  margin-bottom: 3px;
}
.room-sidebar__item-meta {
  font-size: 0.76rem;
  opacity: 0.7;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  margin-top: 2px;
}
</style>
