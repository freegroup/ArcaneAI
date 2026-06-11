<template>
  <div class="room-wrapper" v-if="room">
    <div class="room-layout">
      <div class="config-view">
        <!-- Header — same pattern as welcome-header / personality-header -->
        <div class="room-header">
          <div class="room-header__title">
            <span>{{ room.name }}</span>
            <span v-if="isStart" class="room-header__badge">START</span>
            <span v-if="isEnd" class="room-header__badge room-header__badge--end">END</span>
            <HelpButton @click="showHelp = true" />
            <span class="room-header__map-links" v-if="containingViews.length > 0">
              <router-link
                v-for="v in containingViews"
                :key="v.viewId"
                :to="v.routePath"
                class="room-header__map-link"
                :title="`Show in ${v.label}`"
              >
                <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true">
                  <path fill="currentColor" d="M20.5 3l-.16.03L15 5.1 9 3 3.36 4.9c-.21.07-.36.25-.36.48V20.5c0 .28.22.5.5.5l.16-.03L9 18.9l6 2.1 5.64-1.9c.21-.07.36-.25.36-.48V3.5c0-.28-.22-.5-.5-.5zM10 5.47l4 1.4v11.66l-4-1.4V5.47zm-5 .99l3-1.01v11.7l-3 1.16V6.46zm14 11.08l-3 1.01V6.86l3-1.16v11.84z"/>
                </svg>
                <span class="room-header__map-link-label">{{ v.label }}</span>
              </router-link>
            </span>
          </div>
        </div>

        <!-- Editor — full height like Personality / WelcomePrompt -->
        <Codemirror
          class="full-height-editor"
          :class="{ 'editor-collapsed': aiAssistExpanded }"
          v-model:value="roomText"
          :options="cmOptions"
          placeholder="Describe what the player sees in this room..."
        />

        <!-- AI Assist Expandable Panel — identical structure -->
        <div class="ai-assist-panel">
          <div
            class="ai-assist-header"
            @click="toggleAiAssist"
          >
            <v-icon size="small">{{ aiAssistExpanded ? 'mdi-chevron-up' : 'mdi-chevron-down' }}</v-icon>
            <AIAssistLabel />
          </div>

          <transition name="expand">
            <div v-if="aiAssistExpanded" class="ai-assist-content">
              <div class="ai-response-area">
                <div v-if="!aiResponse && !aiLoading">
                  <AIAssistHelpText />
                </div>

                <AIAssistLoading v-if="aiLoading">AI is working...</AIAssistLoading>

                <div v-if="aiResponse" class="ai-result">
                  <div class="ai-result-header">
                    <strong>Improved Text:</strong>
                    <ThemedButton
                      @click="applyAiResult"
                      title="Apply text to editor"
                    >
                      <v-icon size="small">mdi-check</v-icon>
                      Apply to Editor
                    </ThemedButton>
                  </div>
                  <div class="ai-result-text">{{ aiResponse }}</div>
                  <div v-if="aiComment || wordCountInfo" class="ai-comment">
                    <v-icon size="small" color="info">mdi-comment-text-outline</v-icon>
                    <div>
                      <div v-if="wordCountInfo" class="word-count-info">{{ wordCountInfo }}</div>
                      <div v-if="aiComment">{{ aiComment }}</div>
                    </div>
                  </div>
                </div>
              </div>

              <AIAssistInput
                ref="promptInput"
                v-model="aiPrompt"
                :loading="aiLoading"
                placeholder="e.g. 'Improve the atmosphere' or 'Make it more suspenseful'"
                @send="improveText"
              />
            </div>
          </transition>
        </div>

        <ExtendedHelpDialog
          v-model="showHelp"
          title="Room Description"
          :helpText="helpContent"
        />
      </div>

      <RoomSidebar
        :game-name="gameName"
        :source-id="room.id"
        :ambient-sound="ambientSound"
        :ambient-volume="ambientVolume"
        :triggers="triggers"
        :exits="exits"
        :entries="entries"
        @update:ambient-sound="onAmbientSoundChange"
        @update:ambient-volume="onAmbientVolumeChange"
      />
    </div>
  </div>

  <div v-else class="room-missing">
    <p>Room <code>{{ roomName }}</code> not found.</p>
  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'
import axios from 'axios'

import RoomSidebar from './RoomSidebar.vue'
import ExtendedHelpDialog from '../components/ExtendedHelpDialog.vue'
import HelpButton from '../components/HelpButton.vue'
import ThemedButton from '../components/ThemedButton.vue'
import AIAssistLabel from '../components/AIAssistLabel.vue'
import AIAssistHelpText from '../components/AIAssistHelpText.vue'
import AIAssistLoading from '../components/AIAssistLoading.vue'
import AIAssistInput from '../components/AIAssistInput.vue'

import Codemirror from 'codemirror-editor-vue3'
import 'codemirror/addon/display/placeholder.js'
import 'codemirror/mode/jinja2/jinja2.js'
import 'codemirror/theme/juejin.css'
import 'codemirror/theme/material-darker.css'

const API_BASE_URL = process.env.VUE_APP_API_BASE_URL

export default {
  name: 'RoomDetail',
  components: {
    RoomSidebar, Codemirror,
    ExtendedHelpDialog, HelpButton, ThemedButton,
    AIAssistLabel, AIAssistHelpText, AIAssistLoading, AIAssistInput
  },
  props: {
    gameName: { type: String, required: true },
    roomName: { type: String, required: true }
  },
  data() {
    return {
      // Local editor state — not directly bound to Vuex to keep cursor stable.
      // Synced from store via watcher on roomName, written back via watcher on roomText.
      roomText: '',
      isSyncingFromStore: false,

      cmOptions: {
        mode: 'jinja2',
        lineNumbers: false,
        lineWrapping: true,
        theme: 'material-darker',
        styleActiveLine: false
      },

      showHelp: false,
      helpContent: `
<p>The <strong>Room Description</strong> is what the player "sees" when entering the room.</p>

<p>It provides the context for the LLM — it should convey atmosphere, objects, and mood to the player.</p>

<h4>Tips:</h4>
<ul>
  <li><strong>Sensory details</strong> — sounds, smells, light, temperature</li>
  <li><strong>Concrete objects</strong> — anything the player should be able to interact with must be mentioned here</li>
  <li><strong>Jinja2 conditionals</strong> — e.g. <code>{% if has_key %}...{% endif %}</code> to vary the room based on game state</li>
  <li><strong>Atmosphere over lists</strong> — atmospheric prose, not a bare enumeration</li>
</ul>
      `,

      // AI Assist state
      aiAssistExpanded: false,
      aiPrompt: '',
      aiResponse: '',
      aiComment: '',
      aiLoading: false,
      wordCountInfo: ''
    }
  },
  computed: {
    ...mapGetters('model', ['allStates', 'allConnections']),
    ...mapGetters('views', ['allViews']),
    room() {
      return this.allStates.find(s => s.name === this.roomName) || null
    },
    isStart() {
      return this.room?.stateType === 'START'
    },
    isEnd() {
      return this.room?.stateType === 'END'
    },
    /**
     * All map-views (world + encounters) that contain this room.
     * A view contains the state if it has a layout entry for that state's UUID.
     * Each entry exposes a route path with the room name as a hash, so navigation
     * lands on the right map and the deep-link logic centers the room.
     */
    containingViews() {
      if (!this.room) return []
      const stateId = this.room.id
      const encountersById = this.$store.state.encounters?.encounters || {}
      const hash = encodeURIComponent(this.room.name)
      return this.allViews
        .filter(v => v && v.stateLayouts && v.stateLayouts[stateId])
        .map(v => {
          if (v.viewId === 'world') {
            return {
              viewId: v.viewId,
              label: 'World',
              routePath: `/game/${this.gameName}/world#${hash}`
            }
          }
          // viewId is `encounter_<encounterId>`; route uses the encounter id segment.
          const encounterId = v.viewId.replace(/^encounter_/, '')
          const encounter = encountersById[encounterId]
          return {
            viewId: v.viewId,
            label: encounter?.name || encounterId,
            routePath: `/game/${this.gameName}/encounter/${encounterId}#${hash}`
          }
        })
        // World first, encounters alphabetically after.
        .sort((a, b) => {
          if (a.viewId === 'world') return -1
          if (b.viewId === 'world') return 1
          return a.label.localeCompare(b.label)
        })
    },
    storeText() {
      return this.room?.userData?.system_prompt || ''
    },
    ambientSound() {
      return this.room?.userData?.ambient_sound || null
    },
    ambientVolume() {
      return this.room?.userData?.ambient_sound_volume ?? null
    },
    triggers() {
      return this.room?.trigger || []
    },
    exits() {
      if (!this.room) return []
      const sourceId = this.room.id
      return this.allConnections
        .filter(c => c.source?.node === sourceId)
        .map(c => {
          const targetId = c.target?.node
          const targetState = this.allStates.find(s => s.id === targetId)
          return {
            id: c.id,
            name: c.name,
            description: c.userData?.description,
            conditions: c.userData?.conditions || [],
            targetId,
            targetName: targetState?.name
          }
        })
    },
    entries() {
      if (!this.room) return []
      const targetId = this.room.id
      return this.allConnections
        .filter(c => c.target?.node === targetId)
        .map(c => {
          const sourceId = c.source?.node
          const sourceState = this.allStates.find(s => s.id === sourceId)
          return {
            id: c.id,
            name: c.name,
            description: c.userData?.description,
            conditions: c.userData?.conditions || [],
            sourceId,
            sourceName: sourceState?.name
          }
        })
    }
  },
  watch: {
    // When the user navigates to a different room, refresh the editor from store.
    storeText: {
      immediate: true,
      handler(newVal) {
        if (newVal !== this.roomText) {
          this.isSyncingFromStore = true
          this.roomText = newVal
          this.$nextTick(() => { this.isSyncingFromStore = false })
        }
      }
    },
    // When the user types in the editor, persist to the store.
    roomText(newVal) {
      if (this.isSyncingFromStore || !this.room) return
      if (newVal === this.storeText) return
      this.updateState({
        ...this.room,
        userData: { ...(this.room.userData || {}), system_prompt: newVal }
      })
    }
  },
  methods: {
    ...mapActions('model', ['updateState']),

    onAmbientSoundChange(soundPath) {
      if (!this.room) return
      this.updateState({
        ...this.room,
        userData: { ...(this.room.userData || {}), ambient_sound: soundPath }
      })
    },
    onAmbientVolumeChange(volume) {
      if (!this.room) return
      this.updateState({
        ...this.room,
        userData: { ...(this.room.userData || {}), ambient_sound_volume: volume }
      })
    },

    toggleAiAssist() {
      this.aiAssistExpanded = !this.aiAssistExpanded
      if (this.aiAssistExpanded) {
        this.$nextTick(() => {
          if (this.$refs.promptInput) this.$refs.promptInput.focus()
        })
      }
    },

    countWords(text) {
      return text.trim().split(/\s+/).filter(w => w.length > 0).length
    },

    async improveText() {
      if (!this.aiPrompt.trim()) return

      this.aiLoading = true
      this.aiResponse = ''
      this.aiComment = ''
      this.wordCountInfo = ''

      const wordsBefore = this.countWords(this.roomText)

      try {
        const response = await axios.post(`${API_BASE_URL}/text/improve`, {
          text: this.roomText,
          instruction: this.aiPrompt,
          include_comment: true
        })
        const data = response.data
        this.aiResponse = data.improved_text
        this.aiComment = data.comment || ''
        const wordsAfter = this.countWords(data.improved_text)
        this.wordCountInfo = `Words: ${wordsBefore} → ${wordsAfter}`
        this.aiPrompt = ''
      } catch (error) {
        console.error('AI Improve Text Error:', error)
        this.aiResponse = ''
        this.aiComment = 'Error improving text. Please try again.'
      } finally {
        this.aiLoading = false
      }
    },

    applyAiResult() {
      if (this.aiResponse) {
        this.roomText = this.aiResponse
        this.aiResponse = ''
        this.aiComment = ''
        this.aiPrompt = ''
      }
    }
  }
}
</script>

<style scoped>
/* Wrapper — same pattern as welcome-wrapper / personality-wrapper */
.room-wrapper {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
  box-sizing: border-box;
  height: 100%;
}

.room-layout {
  display: flex;
  flex: 1;
  overflow: hidden;
  position: relative;
}

.config-view {
  flex: 1;
  overflow: hidden;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

/* Header — minimal, theme provides the rest */
.room-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.room-header__title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.room-header__badge {
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  padding: 2px 8px;
  border-radius: 4px;
  background: #d4af37;
  color: #1a1a1a;
}

.room-header__badge--end {
  background: #d9534f;
  color: #fff;
}

.room-header__map-links {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-left: 8px;
}
.room-header__map-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  text-decoration: none;
  color: inherit;
  opacity: 0.7;
  border: 1px solid rgba(127, 127, 127, 0.3);
  border-radius: 4px;
  transition: opacity 0.15s, background 0.15s, border-color 0.15s;
}
.room-header__map-link:hover {
  opacity: 1;
  background: rgba(127, 127, 127, 0.1);
}
.room-header__map-link svg {
  flex-shrink: 0;
}
.room-header__map-link-label {
  white-space: nowrap;
}

/* Editor — same pattern as full-height-editor */
.full-height-editor {
  flex: 1 1 auto;
  position: relative;
  overflow: hidden;
  box-sizing: border-box;
}

.full-height-editor.editor-collapsed {
  /* No height shrinking — see Personality.vue for rationale. */
}

.full-height-editor >>> .CodeMirror-gutters {
  display: none !important;
}

.full-height-editor >>> .codemirror-container {
  position: absolute;
  top: 0; bottom: 0; left: 0; right: 0;
}

.full-height-editor >>> .CodeMirror {
  position: absolute;
  top: 0; bottom: 0; left: 0; right: 0;
  height: 100%;
}

/* AI Assist Panel */
.ai-assist-panel {}

.ai-assist-header {
  display: flex;
  align-items: center;
  cursor: pointer;
  user-select: none;
}

.ai-assist-content {}

.expand-enter-active,
.expand-leave-active {
  overflow: hidden;
}
.expand-enter-from,
.expand-leave-to {
  max-height: 0;
}

.ai-response-area {
  overflow-y: auto;
}

.ai-result {
  display: flex;
  flex-direction: column;
}

.ai-result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.ai-result-text {
  white-space: pre-wrap;
  word-wrap: break-word;
}

.ai-comment {
  display: flex;
  align-items: flex-start;
}

.room-missing {
  padding: 40px;
  text-align: center;
  opacity: 0.7;
}
.room-missing code {
  background: rgba(127, 127, 127, 0.15);
  padding: 1px 6px;
  border-radius: 3px;
}
</style>
