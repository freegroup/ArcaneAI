<template>
    <div class="property-view" v-if="jsonData.type === 'StateShape'">

        <div class="label-with-help">
          <label>State Name</label>
          <HelpButton @click="openHelp('stateName')" />
        </div>
        <input
            id="stateName"
            type="text"
            v-model="jsonData.name"
            @input="onDataChange"
        />

        <!-- Ambient Sound Selection with Finder Dialog -->
        <div class="label-with-help">
          <label>Ambient Sound</label>
          <HelpButton @click="openHelp('ambientSound')" />
        </div>
        <div class="sound-selection">
          <div class="sound-display" @click="showSoundPicker = true">
            <v-icon size="small" class="sound-icon">mdi-music-note</v-icon>
            <span class="sound-name">{{ jsonData.userData.ambient_sound || 'No sound selected' }}</span>
            <v-icon size="small" class="browse-icon">mdi-folder-open</v-icon>
          </div>
          
          <v-btn icon size="small" @click="toggleSound" :disabled="!jsonData.userData.ambient_sound">
            <v-icon size="small">{{ isPlaying ? 'mdi-stop' : 'mdi-play' }}</v-icon>
          </v-btn>
        </div>

        <!-- Sound Picker Dialog -->
        <SoundSelectDialog
          v-model="showSoundPicker"
          :files="soundFiles"
          :currentValue="jsonData.userData.ambient_sound"
          @select="onSoundSelected"
        />
        <div>
          <v-slider
            v-if="jsonData.userData"
            v-model="jsonData.userData.ambient_sound_volume"
            :min="1"
            :max="100"
            :step="1"
            append-icon="mdi-volume-high"
          />
        </div>
        
        <div class="label-with-help" v-if="jsonData.userData">
          <label for="systemPrompt">Scene Description</label>
          <HelpButton @click="openHelp('sceneDescription')" />
        </div>
        <div class="editor-container" v-if="jsonData.userData">
          <Codemirror
              class="code-editor"
              v-model:value="jsonData.userData.system_prompt"
              :options="cmOptions"
              placeholder="test placeholder"
              @change="onDataChange"
          />
          <v-btn 
            icon 
            size="small" 
            class="expand-btn" 
            @click="showJinjaEditor = true"
            title="Open in fullscreen editor"
          >
            <v-icon size="small">mdi-arrow-expand</v-icon>
          </v-btn>
        </div>

        <!-- Help Dialog -->
        <ExtendedHelpDialog
          v-model="showHelpDialog"
          :title="helpTitle"
          :helpText="helpText"
        />

        <!-- Jinja Editor Dialog -->
        <JinjaEditorDialog
          v-model="showJinjaEditor"
          :text="jsonData.userData?.system_prompt || ''"
          @save="updateSystemPrompt"
        />

    </div>
</template>
  
<script>
  import SoundManager from '@/utils/SoundManager'
  import { mapGetters, mapActions } from 'vuex';
  import { MessageTypes, ShapeTypes } from '../../public/shared/SharedConstants.js';
  import ExtendedHelpDialog from '@/components/ExtendedHelpDialog.vue';
  import JinjaEditorDialog from '@/components/JinjaEditorDialog.vue';
  import SoundSelectDialog from '@/components/SoundSelectDialog.vue';
  import HelpButton from '@/components/HelpButton.vue';

  import Codemirror from "codemirror-editor-vue3";
  import "codemirror/addon/display/placeholder.js";
  import "codemirror/mode/jinja2/jinja2.js";
  import "codemirror/addon/display/placeholder.js";
  import "codemirror/theme/juejin.css";
  import "codemirror/theme/material-darker.css";

  export default {
    name: 'PropertyView',
    components: { Codemirror, ExtendedHelpDialog, JinjaEditorDialog, SoundSelectDialog, HelpButton },
    props: {
        draw2dFrame: {
            type: Object,
            required: true,
        },
    },
    data() {
      return {
        jsonData: {
          name: '',
          userData: {
            system_prompt: '',
            ambient_sound: '',
            ambient_sound_volume: 100,
          },
        },
        isInitializing: false,
        cmOptions: {
          mode: "jinja2",
          lineNumbers: false, 
          lineWrapping: true, 
          theme: "material-darker",
          styleActiveLine: false,
        },
        isPlaying: false,
        showHelpDialog: false,
        showJinjaEditor: false,
        showSoundPicker: false,
        helpTitle: '',
        helpText: '',
        helpTexts: {
          stateName: {
            title: 'State Name',
            text: 'The unique identifier for this game state.'
          },
          ambientSound: {
            title: 'Ambient Sound',
            text: 'Background music or ambient sounds that play continuously.'
          },
          sceneDescription: {
            title: 'Scene Description',
            text: 'Describe this location in detail for the AI.'
          }
        }
      };
    },
    computed: {
      ...mapGetters('sounds', ['files']),
      soundFiles() {
        return this.files;
      },
    },
    watch: {
      "jsonData.userData.ambient_sound"() {
        this.onDataLoad();
        if (!this.isInitializing) {
          this.onDataChange();
        }
      },
      "jsonData.userData.ambient_sound_volume"() {
        if (!this.isInitializing) {
          this.onVolumeChange();
        }
      },
    },
    methods: {
      ...mapActions('model', ['updateState']),
      
      onDataLoad() { 
        this.jsonData.name = this.jsonData?.name?.replace(/[^a-zA-Z0-9]/g, '');
        var data = JSON.parse(JSON.stringify( this.jsonData ));
        window.postMessage({ type: MessageTypes.V2C_SET_SHAPE_DATA, data: data }, '*');
      },

      onDataChange() {
        this.onDataLoad();
        if (this.isInitializing) return;
        var data = JSON.parse(JSON.stringify( this.jsonData ));
        this.updateState(data);
      },

      onVolumeChange() {
        if(this.jsonData?.userData){
          const volume = this.jsonData.userData.ambient_sound_volume || 100;
          SoundManager.setVolume(volume);
          this.onDataLoad();
          if (!this.isInitializing) {
            var data = JSON.parse(JSON.stringify( this.jsonData ));
            this.updateState(data);
          }
        }
      },

      toggleSound() {
        if (this.isPlaying) {
          SoundManager.stopCurrentSound();
        } else if (this.jsonData.userData.ambient_sound) {
          const volume = this.jsonData.userData.ambient_sound_volume || 100;
          SoundManager.playSound(this.jsonData.userData.ambient_sound, volume);
        }
      },

      openHelp(fieldKey) {
        const help = this.helpTexts[fieldKey];
        if (help) {
          this.helpTitle = help.title;
          this.helpText = help.text;
          this.showHelpDialog = true;
        }
      },

      updateSystemPrompt(newText) {
        this.jsonData.userData.system_prompt = newText;
        this.onDataChange();
      },

      onSoundSelected(soundPath) {
        this.jsonData.userData.ambient_sound = soundPath;
        this.onDataChange();
      },
    },

    mounted() {
        this.soundListener = SoundManager.addListener((isPlaying) => {
          this.isPlaying = isPlaying;
        });

        this.messageHandler = (event) => {
            if (event.origin !== window.location.origin) return;
            const message = event.data;
            if (message.event === MessageTypes.C2V_SELECT && message.type === ShapeTypes.STATE) {
                SoundManager.stopCurrentSound()
                this.isInitializing = true;
                this.jsonData = message.data;
                if (!this.jsonData.userData.ambient_sound_volume) {
                  this.jsonData.userData.ambient_sound_volume = 100;
                }
                this.$nextTick(() => {
                  this.isInitializing = false;
                });
            }
            else if (message.event === MessageTypes.C2V_UNSELECT) {
                SoundManager.stopCurrentSound()
                this.jsonData = {}
            }
        };
        window.addEventListener('message', this.messageHandler);
    },
    beforeUnmount() {
        if (this.soundListener) {
            this.soundListener();
            this.soundListener = null;
        }
        if (this.messageHandler) {
            window.removeEventListener('message', this.messageHandler);
            this.messageHandler = null;
        }
        SoundManager.stopCurrentSound();
    }
  };
</script>
  
<style scoped>
  ::v-deep .v-input__details { display: none; }
  .property-view {
    background: var(--game-bg-primary);
    color: var(--game-text-primary);
    height: 100%;
    overflow: hidden;
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
  .label-with-help label { display: inline-block !important; margin: 0 !important; }
  .property-view input {
    width: 100%;
    padding: var(--game-spacing-sm) var(--game-spacing-md);
    background: var(--game-input-bg);
    border: 1px solid var(--game-input-border);
    border-radius: 0;
    color: var(--game-text-primary);
    font-size: var(--game-font-size-md);
    transition: all var(--game-transition-fast);
    outline: none;
  }
  .property-view input#stateName {
    font-family: var(--game-font-family-retro);
    font-size: 18px;
    letter-spacing: 2px;
    color: var(--game-accent-secondary);
    text-shadow: 2px 2px 0px rgba(0, 0, 0, 0.5);
    padding: var(--game-spacing-md) var(--game-spacing-lg);
  }
  .property-view input:hover { background: var(--game-input-hover); border-color: var(--game-border-highlight); }
  .property-view input:focus { border-color: var(--game-input-focus); box-shadow: 0 0 0 2px rgba(233, 69, 96, 0.2); }
  .sound-selection { display: flex; align-items: flex-start; gap: var(--game-spacing-sm); }
  .sound-display {
    flex: 1;
    display: flex;
    align-items: center;
    gap: var(--game-spacing-sm);
    padding: var(--game-spacing-sm) var(--game-spacing-md);
    background: var(--game-input-bg);
    border: 1px solid var(--game-input-border);
    cursor: pointer;
    transition: all var(--game-transition-fast);
    min-height: 36px;
  }
  .sound-display:hover { background: var(--game-input-hover); border-color: var(--game-border-highlight); }
  .sound-display .sound-icon { color: var(--game-accent-secondary); flex-shrink: 0; }
  .sound-display .sound-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: var(--game-font-size-sm); color: var(--game-text-primary); }
  .sound-display .browse-icon { color: var(--game-text-muted); flex-shrink: 0; opacity: 0.6; transition: opacity var(--game-transition-fast); }
  .sound-display:hover .browse-icon { opacity: 1; color: var(--game-accent-secondary); }
  .sound-selection :deep(.v-btn) {
    background: var(--game-accent-primary) !important;
    color: var(--game-text-primary) !important;
    border-radius: 0 !important;
    min-width: 36px !important;
    height: 36px !important;
  }
  :deep(.v-slider) { margin-top: var(--game-spacing-sm); }
  :deep(.v-slider-track__fill) { background: var(--game-accent-primary) !important; }
  :deep(.v-slider-thumb__surface) { background: var(--game-accent-primary) !important; }
  .editor-container { position: relative; flex: 1; display: flex; flex-direction: column; min-height: 0; overflow: hidden; }
  .expand-btn { position: absolute; top: 8px; right: 8px; z-index: 10; background: var(--game-accent-primary) !important; opacity: 0.33; }
  .expand-btn:hover { opacity: 1; }
  .code-editor { flex: 1; display: flex; flex-direction: column; min-height: 0; }
  .code-editor :deep(.CodeMirror) {
    font-size: var(--game-font-size-md);
    font-family: var(--game-font-family-mono);
    background: var(--game-input-bg);
    color: var(--game-text-primary);
    border: 1px solid var(--game-input-border);
    border-radius: 0;
    padding: var(--game-spacing-sm);
    height: 100%;
  }
  .label-with-help { display: inline-flex; align-items: center; gap: 4px; margin-bottom: var(--game-spacing-xs); }
</style>