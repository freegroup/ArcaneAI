 <template>
    <div class="property-view" v-if="jsonData.type === 'StateShape'">

        <div class="label-with-help">
          <label>State Name</label>
          <v-btn icon size="x-small" @click="openHelp('stateName')" class="help-btn">
            <v-icon size="small">mdi-information-outline</v-icon>
          </v-btn>
        </div>
        <input
            id="stateName"
            type="text"
            v-model="jsonData.name"
            @input="onDataChange"
        />

        <!-- Ambient Sound ComboBox and Play Button -->
        <div class="label-with-help">
          <label>Ambient Sound</label>
          <v-btn icon size="x-small" @click="openHelp('ambientSound')" class="help-btn">
            <v-icon size="small">mdi-information-outline</v-icon>
          </v-btn>
        </div>
        <div class="sound-selection">
          <v-select
            v-model="jsonData.userData.ambient_sound"
            :items="soundFiles"
            density="compact"
            label="Ambient Sound"
            :items-per-page="1000"
            :list-props="{maxWidth:'350px', minWidth: '350px'}"
            outlined
          ></v-select>
          
          <v-btn icon size="small" @click="toggleSound">
            <v-icon size="small">{{ isPlaying ? 'mdi-stop' : 'mdi-play' }}</v-icon>
          </v-btn>
        </div>
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
          <label for="systemPrompt">Sceen Description</label>
          <v-btn icon size="x-small" @click="openHelp('sceneDescription')" class="help-btn">
            <v-icon size="small">mdi-information-outline</v-icon>
          </v-btn>
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
  import { mapGetters } from 'vuex';
  import MessageTypes from '../../public/canvas/MessageTypes.js';
  import ExtendedHelpDialog from '@/components/ExtendedHelpDialog.vue';
  import JinjaEditorDialog from '@/components/JinjaEditorDialog.vue';

  import Codemirror from "codemirror-editor-vue3";
  import "codemirror/addon/display/placeholder.js";
  import "codemirror/mode/jinja2/jinja2.js";
  import "codemirror/addon/display/placeholder.js";
  import "codemirror/theme/juejin.css";
  import "codemirror/theme/material-darker.css";

  export default {
    name: 'PropertyView',
    components: { Codemirror, ExtendedHelpDialog, JinjaEditorDialog },
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
        cmOptions: {
          mode: "jinja2",
          lineNumbers: false, 
          lineWrapping: true, 
          theme: "material-darker",
          styleActiveLine: false,
        },
        isPlaying: false,
        // Help Dialog
        showHelpDialog: false,
        // Jinja Editor Dialog
        showJinjaEditor: false,
        helpTitle: '',
        helpText: '',
        helpTexts: {
          stateName: {
            title: 'State Name',
            text: 'The unique identifier for this game state. Use only letters and numbers. This name will be displayed in the game map and used to reference this state in transitions.'
          },
          ambientSound: {
            title: 'Ambient Sound',
            text: 'Background music or ambient sounds that play continuously while the player is in this state. Choose a sound file that matches the atmosphere you want to create for this location.'
          },
          sceneDescription: {
            title: 'Scene Description',
            text: 'Describe this location in detail. This text will be used by the AI to understand the scene and generate appropriate responses. Include atmosphere, objects, NPCs, and possible interactions. You can use Jinja2 template syntax to reference game state variables and inventory items. Use conditional blocks ({% if inventory.key %}...{% endif %}) to show or hide text based on what the player has, giving the AI more or less context dynamically.'
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
        this.onDataChange();
      },
      "jsonData.userData.ambient_sound_volume"() {
        this.onVolumeChange();
      },
    },
    methods: {

      onDataChange() { 
        this.jsonData.name = this.jsonData?.name?.replace(/[^a-zA-Z0-9]/g, '');
        if (this.draw2dFrame ) {
            console.log('📝 [SYNC] Vue → Canvas: StateShape data changed', {
              name: this.jsonData.name,
              hasSystemPrompt: !!this.jsonData.userData?.system_prompt,
              ambientSound: this.jsonData.userData?.ambient_sound || 'none'
            });
            var data = JSON.parse(JSON.stringify( this.jsonData ));
            this.draw2dFrame.postMessage({ type: MessageTypes.SET_SHAPE_DATA, data: data },'*');
        }
      },

      onVolumeChange() {
        if(this.jsonData?.userData){
          const volume = this.jsonData.userData.ambient_sound_volume || 100;
          SoundManager.setVolume(volume);
          this.onDataChange();
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
    },

    mounted() {
        // Listen to SoundManager events
        this.soundListener = SoundManager.addListener((isPlaying) => {
          this.isPlaying = isPlaying;
        });

        // Event listener for messages from the iframe
        this.messageHandler = (event) => {
            if (event.origin !== window.location.origin) return;
            const message = event.data;
            if (message.event === MessageTypes.SELECT && message.type === MessageTypes.SHAPE_STATE) {
                console.log('🎯 [SYNC] Canvas → Vue: StateShape selected', {
                  name: message.data?.name,
                  hasAmbientSound: !!message.data?.userData?.ambient_sound
                });
                SoundManager.stopCurrentSound()
                this.jsonData = message.data;
                if (!this.jsonData.userData.ambient_sound_volume) {
                  this.jsonData.userData.ambient_sound_volume = 100;
                }
            }
            else if (message.event === MessageTypes.UNSELECT) {
                console.log('❌ [SYNC] Canvas → Vue: Selection cleared');
                SoundManager.stopCurrentSound()
                this.jsonData = {}
            }
        };
        window.addEventListener('message', this.messageHandler);
    },
    beforeUnmount() {
        // Clean up sound listener
        if (this.soundListener) {
            this.soundListener();
            this.soundListener = null;
        }
        // Clean up event listener to prevent memory leaks
        if (this.messageHandler) {
            window.removeEventListener('message', this.messageHandler);
            this.messageHandler = null;
        }
        // Stop any playing sounds when component is destroyed
        SoundManager.stopCurrentSound();
    }
  };
  </script>
  
<style scoped>
  ::v-deep .v-input__details {
    display: none;
  }

  .property-view {
    background: var(--game-bg-primary);
    color: var(--game-text-primary);
    height: 100%;
    overflow-y: auto;
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

  /* Override for labels inside label-with-help */
  .label-with-help label {
    display: inline-block !important;
    margin: 0 !important;
  }

  .property-view input {
    width: 100%;
    padding: var(--game-spacing-sm) var(--game-spacing-md);
    background: var(--game-input-bg);
    border: 1px solid var(--game-input-border);
    border-radius: var(--game-radius-md);
    color: var(--game-text-primary);
    font-size: var(--game-font-size-md);
    transition: all var(--game-transition-fast);
    outline: none;
  }

  /* Retro 8-Bit Font for State Name */
  .property-view input#stateName {
    font-family: var(--game-font-family-retro);
    font-size: 18px;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: var(--game-accent-secondary);
    text-shadow: 2px 2px 0px rgba(0, 0, 0, 0.5);
    padding: var(--game-spacing-md) var(--game-spacing-lg);
  }

  .property-view input:hover {
    background: var(--game-input-hover);
    border-color: var(--game-border-highlight);
  }

  .property-view input:focus {
    border-color: var(--game-input-focus);
    box-shadow: 0 0 0 2px rgba(233, 69, 96, 0.2);
  }

  .sound-selection {
    display: flex;
    align-items: flex-start;
    gap: var(--game-spacing-sm);
  }

  .sound-selection :deep(.v-select) {
    flex: 1;
  }

  .sound-selection :deep(.v-field) {
    background: var(--game-input-bg);
    border: 1px solid var(--game-input-border);
    border-radius: var(--game-radius-md);
  }

  .sound-selection :deep(.v-field:hover) {
    background: var(--game-input-hover);
    border-color: var(--game-border-highlight);
  }

  .sound-selection :deep(.v-btn) {
    background: var(--game-accent-primary);
    color: var(--game-text-primary);
    border-radius: var(--game-radius-md);
    transition: all var(--game-transition-fast);
  }

  .sound-selection :deep(.v-btn:hover) {
    background: var(--game-accent-tertiary);
    box-shadow: var(--game-shadow-glow);
  }

  /* Slider Styling - Vuetify 3 */
  :deep(.v-slider) {
    margin-top: var(--game-spacing-sm);
  }

  :deep(.v-slider-track__background) {
    background: var(--game-border-color) !important;
    opacity: 1 !important;
  }

  :deep(.v-slider-track__fill) {
    background: var(--game-accent-primary) !important;
  }

  :deep(.v-slider-thumb__surface) {
    background: var(--game-accent-primary) !important;
    width: 20px !important;
    height: 20px !important;
    border-radius: 50% !important;
    border: 2px solid var(--game-bg-primary) !important;
    box-shadow: var(--game-shadow-md) !important;
  }

  :deep(.v-slider-thumb:hover .v-slider-thumb__surface) {
    transform: scale(1.1);
  }

  /* Editor Container with Expand Button */
  .editor-container {
    position: relative;
  }

  .expand-btn {
    position: absolute;
    top: 8px;
    right: 8px;
    z-index: 10;
    background: var(--game-accent-primary) !important;
    color: var(--game-text-primary) !important;
    box-shadow: var(--game-shadow-md);
    transition: all var(--game-transition-fast);
  }

  .expand-btn:hover {
    background: var(--game-accent-tertiary) !important;
    box-shadow: var(--game-shadow-glow);
    transform: scale(1.1);
  }

  .expand-btn :deep(.v-icon) {
    font-size: 18px !important;
  }

  /* CodeMirror Game Theme */
  .code-editor :deep(.CodeMirror) {
    font-size: var(--game-font-size-md);
    font-family: var(--game-font-family-mono);
    background: var(--game-input-bg);
    color: var(--game-text-primary);
    border: 1px solid var(--game-input-border);
    border-radius: var(--game-radius-md);
    padding: var(--game-spacing-sm);
    min-height: 120px;
  }

  .code-editor :deep(.CodeMirror-gutters) {
    display: none;
  }

  .code-editor :deep(.CodeMirror-cursor) {
    border-left-color: var(--game-accent-primary);
  }

  .code-editor :deep(.CodeMirror-selected) {
    background: rgba(233, 69, 96, 0.2);
  }

  /* Label with Help Icon */
  .label-with-help {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    margin-bottom: var(--game-spacing-xs);
  }

  .label-with-help label {
    margin: 0;
    display: inline-block;
  }

  .help-btn {
    background: transparent !important;
    color: var(--game-text-secondary) !important;
    transition: all var(--game-transition-fast);
    min-width: unset !important;
    padding: 0 !important;
    width: 20px !important;
    height: 20px !important;
  }

  .help-btn :deep(.v-icon) {
    font-size: 20px !important;
  }

  .help-btn:hover {
    color: var(--game-accent-secondary) !important;
    transform: scale(1.15);
  }
</style>
  