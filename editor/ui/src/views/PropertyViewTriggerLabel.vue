<template>
    <div class="property-view"  v-if="jsonData.type === 'TriggerLabel'">

        <div class="label-with-help">
          <label>Trigger Name</label>
          <HelpButton @click="openHelp('triggerName')" />
        </div>
        <input
            id="stateName"
            type="text"
            lable="Name"
            v-model="jsonData.text"
            @input="onDataChange"
        />

        <!-- Sound Effect Selection with Finder Dialog -->
        <div class="label-with-help">
          <label>Sound Effect</label>
          <HelpButton @click="openHelp('soundEffect')" />
        </div>
        <div class="sound-selection">
          <div class="sound-display" @click="showSoundPicker = true">
            <v-icon size="small" class="sound-icon">mdi-music-note</v-icon>
            <span class="sound-name">{{ jsonData.userData.sound_effect || 'No sound selected' }}</span>
            <v-icon size="small" class="browse-icon">mdi-folder-open</v-icon>
          </div>
          <v-btn icon size="small" @click="toggleSound" :disabled="!jsonData.userData.sound_effect">
            <v-icon size="small">{{ isPlaying ? 'mdi-stop' : 'mdi-play' }}</v-icon>
          </v-btn>
        </div>

        <!-- Sound Picker Dialog -->
        <SoundPickerDialog
          v-model="showSoundPicker"
          :files="soundFiles"
          :currentValue="jsonData.userData.sound_effect"
          @select="onSoundSelected"
        />

        <div class="sound-duration" v-if="jsonData.userData.sound_effect">
          <v-text-field
            v-model.number="jsonData.userData.sound_effect_duration"
            label="Sound Effect Duration"
            :suffix="'seconds'"
            density="compact"
            type="number"
            min="0"
            max="600"
            @input="onDataChange"
            append-icon="mdi-clock"
            outlined
          />
        </div>

        <div>
          <v-slider
            v-if="jsonData.userData"
            v-model="jsonData.userData.sound_effect_volume"
            :min="1"
            :max="100"
            :step="1"
            append-icon="mdi-volume-high"
          />
        </div>
        
        <div style="flex:1;display:flex;flex-direction: column;min-height:0;">
          <div class="label-with-help" v-if="jsonData.userData">
            <label for="triggerDescription">Action Description</label>
            <HelpButton @click="openHelp('actionDescription')" />
          </div>
          <div class="editor-container" style="flex:1;min-height:0;" v-if="jsonData.userData">
            <textarea
                id="triggerDescription"
                v-model="jsonData.userData.description"
                @input="onDataChange"
                placeholder="Describe what possible happen on this action"
            ></textarea>
            <v-btn 
              icon 
              size="small" 
              class="expand-btn" 
              @click="showActionEditor = true"
              title="Open in fullscreen editor"
            >
              <v-icon size="small">mdi-arrow-expand</v-icon>
            </v-btn>
          </div>
        </div>

        <div style="flex:1;display:flex;flex-direction: column;min-height:0;">
          <div class="label-with-help" v-if="jsonData.userData">
            <label for="systemPrompt">On Success</label>
            <HelpButton @click="openHelp('onSuccess')" />
          </div>
          <div class="editor-container" style="flex:1;min-height:0;" v-if="jsonData.userData">
            <textarea
                id="systemPrompt"
                v-model="jsonData.userData.system_prompt"
                @input="onDataChange"
                placeholder="Enter what happens on success of the action"
            ></textarea>
            <v-btn 
              icon 
              size="small" 
              class="expand-btn" 
              @click="showSuccessEditor = true"
              title="Open in fullscreen editor"
            >
              <v-icon size="small">mdi-arrow-expand</v-icon>
            </v-btn>
          </div>
        </div>

        <div>
          <div class="label-with-help">
            <label for="conditions">Conditions</label>
            <HelpButton @click="openHelp('conditions')" />
          </div>
          <textarea
            id="conditions"
            v-model="conditionsText"
            @input="updateConditions"
            placeholder="Enter each condition on a new line"
          ></textarea>
        </div>

        <div>
          <div class="label-with-help">
            <label for="actions">Actions</label>
            <HelpButton @click="openHelp('actions')" />
          </div>
          <textarea
            id="actions"
            v-model="actionsText"
            @input="updateActions"
            placeholder="Enter each action on a new line"
          ></textarea>
        </div>

        <!-- Help Dialog -->
        <ExtendedHelpDialog
          v-model="showHelpDialog"
          :title="helpTitle"
          :helpText="helpText"
        />

        <!-- Jinja Editor Dialogs -->
        <JinjaEditorDialog
          v-model="showActionEditor"
          :text="jsonData.userData?.description || ''"
          @save="updateActionDescription"
        />
        <JinjaEditorDialog
          v-model="showSuccessEditor"
          :text="jsonData.userData?.system_prompt || ''"
          @save="updateOnSuccess"
        />

    </div>
  </template>
  
<script>
  import SoundManager from '@/utils/SoundManager'
  import { mapGetters } from 'vuex';
  import MessageTypes from '../../public/canvas/MessageTypes.js';
  import ExtendedHelpDialog from '@/components/ExtendedHelpDialog.vue';
  import JinjaEditorDialog from '@/components/JinjaEditorDialog.vue';
  import SoundPickerDialog from '@/components/SoundPickerDialog.vue';
  import HelpButton from '@/components/HelpButton.vue';
  import "codemirror/theme/material-darker.css";

  export default {
    name: 'PropertyView',
    components: { ExtendedHelpDialog, JinjaEditorDialog, SoundPickerDialog, HelpButton },
    props: {
        draw2dFrame: {
            type: Object,
            required: true,
        },
    },
    data() {
      return {
        jsonData: {
          text: "",
          userData: {
            system_prompt: '',
            actions: [], 
            conditions: [], 
            sound_effect: '',
            sound_effect_volume: 100,
            sound_effect_duration: 2,
            description: '',
          },
        },
        conditionsText: '',
        actionsText: '',
        isPlaying: false,
        // Help Dialog
        showHelpDialog: false,
        // Jinja Editor Dialogs
        showActionEditor: false,
        showSuccessEditor: false,
        // Sound Picker Dialog
        showSoundPicker: false,
        helpTitle: '',
        helpText: '',
        helpTexts: {
          triggerName: {
            title: 'Trigger Name',
            text: `<strong>The Unique Identifier for this Action</strong><br><br>
            Use descriptive names like <code>open_door</code> or <code>take_key</code>. This name is used internally and helps you organize your game logic.<br><br>
            <strong>🎯 AI Matching Importance:</strong><br>
            A well-chosen, descriptive name also helps the AI match this action with player input more accurately. The clearer and more specific the name, the better the AI can identify and execute the correct trigger when the player expresses their intent.<br><br>
            <strong>Good Examples:</strong>
            <ul>
              <li><code>open_door</code> - Clear and specific ✅</li>
              <li><code>take_key</code> - Describes exact action ✅</li>
              <li><code>examine_chest</code> - Detailed action ✅</li>
              <li><code>talk_to_merchant</code> - Specific interaction ✅</li>
            </ul>
            <strong>Bad Examples:</strong>
            <ul>
              <li><code>action1</code> - Not descriptive ❌</li>
              <li><code>do_something</code> - Too vague ❌</li>
              <li><code>x</code> - No meaning ❌</li>
            </ul>`
          },
          soundEffect: {
            title: 'Sound Effect',
            text: 'A sound effect that plays when this trigger activates. Choose a sound that matches the action, like a door opening, footsteps, or an item pickup. The sound provides audio feedback to enhance player immersion.'
          },
          actionDescription: {
            title: 'Action Description',
            text: 'Describe this action in detail. The AI uses this text to match player input against available actions. Be specific about what the player wants to do (e.g., "open the door", "take the key", "examine the chest"). If the AI determines that the player\'s input matches this action description, the trigger will execute. The better you describe the action, the more accurately the AI can recognize player intent.'
          },
          onSuccess: {
            title: 'On Success',
            text: 'Text that the AI will use when this action succeeds. Describe the result of the action from the player\'s perspective. This will be included in the AI\'s response to create a cohesive narrative experience.'
          },
          conditions: {
            title: 'Conditions',
            text: `<strong>Prerequisites for this Action</strong><br><br>
            Conditions must be met for the AI system to consider this action. If conditions are not fulfilled, the action cannot be executed.<br><br>
            <strong>Example:</strong><br>
            For the action "open_door", the condition could be:<br>
            <code>has_key == true</code><br><br>
            <strong>Meaning:</strong> Without a key in the inventory, the door cannot be opened. The AI will only execute the "open_door" action when the player has a key.<br><br>
            <strong>More Examples:</strong>
            <ul>
              <li><code>torch == true</code> - Player must have torch</li>
              <li><code>coins >= 5</code> - At least 5 coins required</li>
              <li><code>door_unlocked == true</code> - Door must be unlocked</li>
              <li><code>boss_defeated == true</code> - Boss must be defeated</li>
            </ul>
            <strong>Important:</strong> All conditions must be true (AND logic). One condition per line.`
          },
          actions: {
            title: 'Actions',
            text: `<strong>What Happens When Action Succeeds</strong><br><br>
            Actions are executed when the trigger activates successfully. Use this to modify the game state and update the player's inventory. Enter one action per line.<br><br>
            <strong>Example:</strong><br>
            For the action "collect_coin", you could update the inventory:<br>
            <code>coins = coins + 1</code><br><br>
            <strong>Meaning:</strong> When the player collects a coin, the coins value in their inventory increases by 1. This updates the player's inventory automatically.<br><br>
            <strong>More Examples:</strong>
            <ul>
              <li><code>has_key = true</code> - Add key to inventory</li>
              <li><code>torch = false</code> - Remove torch from inventory</li>
              <li><code>health = health - 10</code> - Reduce health by 10</li>
              <li><code>door_unlocked = true</code> - Unlock a door (state variable)</li>
              <li><code>boss_defeated = true</code> - Mark boss as defeated</li>
            </ul>
            <strong>Important:</strong> Actions modify inventory items and game state variables. One action per line.`
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
    methods: {
      onDataChange() { 
        this.jsonData.text = this.jsonData?.text?.replace(/[^a-zA-Z0-9_-]/g, '');
        if (this.draw2dFrame ) {
            console.log('📝 [SYNC] Vue → Canvas: TriggerLabel data changed', {
              name: this.jsonData.text,
              soundEffect: this.jsonData.userData?.sound_effect || 'none',
              hasConditions: this.jsonData.userData?.conditions?.length > 0,
              hasActions: this.jsonData.userData?.actions?.length > 0
            });
            var data = JSON.parse(JSON.stringify( this.jsonData ));
            this.draw2dFrame.postMessage({ type: MessageTypes.SET_SHAPE_DATA, data: data },'*');
        }
      },
      onVolumeChange() {
        if(this.jsonData?.userData){
          const volume = this.jsonData.userData.sound_effect_volume || 100;
          SoundManager.setVolume(volume);
          this.onDataChange();
        }
      },
      updateConditions() {
        const trimmedText = this.conditionsText?.trim();
        if (trimmedText === "" || trimmedText.split('\n').every(line => line.trim() === "")) {
          this.jsonData.userData.conditions = [];
        } else {
          this.jsonData.userData.conditions = trimmedText.split('\n').map(line => line.trim());
        }
        this.onDataChange();
      },
      updateActions() {
        // Split text by line and update jsonData.userData.actions
        this.jsonData.userData.actions = this.actionsText?.split('\n') ?? [];
        this.onDataChange();
      },
      toggleSound() {
        if (this.isPlaying) {
          SoundManager.stopCurrentSound();
        } else if (this.jsonData.userData.sound_effect) {
          const volume = this.jsonData.userData.sound_effect_volume || 100;
          SoundManager.playSound(this.jsonData.userData.sound_effect, volume);
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

      updateActionDescription(newText) {
        this.jsonData.userData.description = newText;
        this.onDataChange();
      },

      updateOnSuccess(newText) {
        this.jsonData.userData.system_prompt = newText;
        this.onDataChange();
      },

      onSoundSelected(soundPath) {
        this.jsonData.userData.sound_effect = soundPath;
        this.onDataChange();
      },
    },
    watch: {
      // Watch jsonData for changes to update the text areas if jsonData changes
      'jsonData.userData.conditions': {
        handler(newConditions) {
          this.conditionsText = newConditions?.join('\n') ?? "";
        },
        immediate: true,
      },
      'jsonData.userData.actions': {
        handler(newActions) {
          this.actionsText = newActions?.join('\n') ?? "";
        },
        immediate: true,
      },
      "jsonData.userData.sound_effect"() {
          this.onDataChange();
      },
      "jsonData.userData.sound_effect_volume"() {
        this.onVolumeChange();
      },
      "jsonData.userData.description"() {
          this.onDataChange();
      },
      "jsonData.userData.sound_effect_duration"() {
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
            if (message.event === MessageTypes.SELECT && message.type === MessageTypes.SHAPE_TRIGGER_LABEL) {
                console.log('🎯 [SYNC] Canvas → Vue: TriggerLabel selected', {
                  name: message.data?.text,
                  hasSoundEffect: !!message.data?.userData?.sound_effect
                });
                SoundManager.stopCurrentSound()

                this.jsonData = message.data
                this.jsonData.userData.sound_effect_volume ??= 100;
                // 0 is allowed as well
                if (this.jsonData.userData.sound_effect_duration === null) {
                    this.jsonData.userData.sound_effect_duration = 2;
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
    min-height:900px;
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

  /* Retro 8-Bit Font for Trigger Name */
  .property-view input#stateName {
    font-family: var(--game-font-family-retro);
    font-size: 18px;
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

  .property-view textarea {
    width: 100%;
    padding: var(--game-spacing-sm) var(--game-spacing-md);
    background: var(--game-input-bg);
    border: 1px solid var(--game-input-border);
    border-radius: var(--game-radius-md);
    color: var(--game-text-primary);
    font-size: var(--game-font-size-md);
    font-family: var(--game-font-family-mono);
    resize: vertical;
    min-height: 80px;
    transition: all var(--game-transition-fast);
    outline: none;
    overflow-y: auto;
  }

  /* Textareas in flex containers */
  .editor-container textarea {
    height: 100%;
    resize: none;
  }

  .property-view textarea:hover {
    background: var(--game-input-hover);
    border-color: var(--game-border-highlight);
  }

  .property-view textarea:focus {
    border-color: var(--game-input-focus);
    box-shadow: 0 0 0 2px rgba(233, 69, 96, 0.2);
  }

  .sound-selection {
    display: flex;
    align-items: flex-start;
    gap: var(--game-spacing-sm);
  }

  /* Sound Display - clickable field to open picker */
  .sound-display {
    flex: 1;
    display: flex;
    align-items: center;
    gap: var(--game-spacing-sm);
    padding: var(--game-spacing-sm) var(--game-spacing-md);
    background: var(--game-input-bg);
    border: 1px solid var(--game-input-border);
    border-radius: var(--game-radius-md);
    cursor: pointer;
    transition: all var(--game-transition-fast);
    min-height: 36px;
  }

  .sound-display:hover {
    background: var(--game-input-hover);
    border-color: var(--game-border-highlight);
  }

  .sound-display .sound-icon {
    color: var(--game-accent-secondary);
    flex-shrink: 0;
  }

  .sound-display .sound-name {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: var(--game-font-size-sm);
    color: var(--game-text-primary);
  }

  .sound-display .browse-icon {
    color: var(--game-text-muted);
    flex-shrink: 0;
    opacity: 0.6;
    transition: opacity var(--game-transition-fast);
  }

  .sound-display:hover .browse-icon {
    opacity: 1;
    color: var(--game-accent-secondary);
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

  .sound-duration :deep(.v-text-field) {
    margin-top: var(--game-spacing-sm);
  }

  .sound-duration :deep(.v-field) {
    background: var(--game-input-bg);
    border: 1px solid var(--game-input-border);
    border-radius: var(--game-radius-md);
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
    opacity: 0.33;
    min-width: 28px !important;
    width: 28px !important;
    height: 28px !important;
  }

  .expand-btn:hover {
    background: var(--game-accent-tertiary) !important;
    box-shadow: var(--game-shadow-glow);
    transform: scale(1.1);
    opacity: 1;
  }

  .expand-btn :deep(.v-icon) {
    font-size: 18px !important;
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

</style>
  