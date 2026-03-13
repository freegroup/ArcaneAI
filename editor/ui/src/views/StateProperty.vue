<template>
    <div class="property-view" v-if="jsonData.type === 'StateShape'">

        <div class="field-group">
          <div class="label-with-help">
            <label>State Name</label>
            <HelpButton @click="openHelp('stateName')" />
          </div>
          <input
              ref="nameInput"
              id="stateName"
              type="text"
              v-model="jsonData.name"
              @input="onDataChange"
          />
        </div>

        <!-- Ambient Sound Selection with Finder Dialog -->
        <div class="field-group">
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
        </div>
        
        <div class="property-view__section">
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
            <ExpandButton @click="showJinjaEditor = true" />
          </div>
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
  import ExpandButton from '@/components/ExpandButton.vue';

  import Codemirror from "codemirror-editor-vue3";
  import "codemirror/addon/display/placeholder.js";
  import "codemirror/mode/jinja2/jinja2.js";
  import "codemirror/addon/display/placeholder.js";
  import "codemirror/theme/juejin.css";
  import "codemirror/theme/material-darker.css";

  export default {
    name: 'PropertyView',
    components: { Codemirror, ExtendedHelpDialog, JinjaEditorDialog, SoundSelectDialog, HelpButton, ExpandButton },
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
            text: `<p>A label to identify this state in your diagram.</p>

<p><strong>Good to know:</strong></p>
<ul>
  <li>This name is <em>just for you</em> — it helps you navigate</li>
  <li>It has <strong>no effect</strong> on the AI or game behavior</li>
  <li>Choose names that are meaningful and easy to remember</li>
</ul>

<p><strong>Tips:</strong></p>
<ul>
  <li>Use descriptive names like "TavernEntrance" or "BossFight"</li>
  <li>Keep it short but recognizable</li>
  <li>Only letters and numbers are allowed</li>
</ul>`
          },
          ambientSound: {
            title: 'Ambient Sound',
            text: `<p>Select a background sound that plays continuously in this scene.</p>

<p><strong>Purpose:</strong></p>
<ul>
  <li>Sets the emotional tone and atmosphere</li>
  <li>Reinforces the feeling you want to evoke</li>
  <li>Immerses the player deeper into the scene</li>
</ul>

<p><strong>Examples:</strong></p>
<ul>
  <li><em>Tavern</em> → crowd chatter, clinking glasses</li>
  <li><em>Forest</em> → birds, rustling leaves, wind</li>
  <li><em>Dungeon</em> → dripping water, distant echoes</li>
  <li><em>Battle</em> → tense music, war drums</li>
</ul>

<p>Choose sounds that support the mood you want players to feel.</p>`
          },
          sceneDescription: {
            title: 'Scene Description',
            text: `<p>Describe this location vividly for the game engine. A rich description helps the AI create immersive, authentic responses.</p>

<p><strong>Include sensory details:</strong></p>
<ul>
  <li>What the player <em>sees</em> (lighting, colors, objects)</li>
  <li>What they <em>hear</em> (ambient sounds, echoes)</li>
  <li>What they <em>smell</em> (smoke, flowers, decay)</li>
  <li>The <em>atmosphere</em> (mood, tension, comfort)</li>
</ul>

<p><strong>Best practices:</strong></p>
<ul>
  <li>Be specific but concise</li>
  <li>Focus on details that matter for player interaction</li>
  <li>Avoid excessive prose that may confuse the AI</li>
</ul>`
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

      /**
       * Focus a specific property field.
       * @param {string} fieldName - The field to focus ('name', etc.)
       */
      focusField(fieldName) {
        this.$nextTick(() => {
          if (fieldName === 'name' && this.$refs.nameInput) {
            this.$refs.nameInput.focus();
            this.$refs.nameInput.select();
          }
        });
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
            // Handle focus request from canvas (e.g., after adding new element)
            else if (message.type === MessageTypes.C2V_FOCUS_PROPERTY) {
                this.focusField(message.field);
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
    height: 100%;
    overflow-y: auto;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
  }
  .label-with-help label { display: inline-block !important; }
  .property-view textarea {
    resize: vertical;
    flex: 1;
  }
  .sound-selection { display: flex; align-items: flex-start; }
  .sound-display {
    flex: 1;
    display: flex;
    align-items: center;
    cursor: pointer;
  }
  .sound-display .sound-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .sound-display .sound-icon { flex-shrink: 0; }
  .sound-display .browse-icon { flex-shrink: 0; }
  .property-view__section {
    flex: 1;
    display: flex;
    flex-direction: column;
  }
  .editor-container {
    position: relative;
    flex: 1;
    display: flex;
    flex-direction: column;
  }
  .code-editor { flex: 1; display: flex; flex-direction: column; }
  .field-group { display: flex; flex-direction: column; }
  .label-with-help { display: inline-flex; align-items: center; }
</style>