<template>
    <div class="property-view"  v-if="jsonData.type === 'TriggerLabel'">

        <div class="field-group">
          <div class="label-with-help">
            <label>Action Name</label>
            <HelpButton @click="openHelp('triggerName')" />
          </div>
          <input
              id="stateName"
              type="text"
              lable="Name"
              v-model="jsonData.text"
              @input="onDataChange"
          />
        </div>

        <!-- Sound Effect Selection with Finder Dialog -->
        <div class="field-group">
          <div class="label-with-help">
            <label>Sound Effect</label>
            <HelpButton @click="openHelp('soundEffect')" />
          </div>
          <div class="sound-selection">
          <div class="sound-display" @click="showSoundPicker = true">
            <span class="sound-name">{{ jsonData.userData.sound_effect || 'No sound selected' }}</span>
            <v-icon size="small" class="browse-icon">mdi-folder-open</v-icon>
          </div>
            <v-btn icon size="small" @click="toggleSound" :disabled="!jsonData.userData.sound_effect">
              <v-icon size="small">{{ isPlaying ? 'mdi-stop' : 'mdi-play' }}</v-icon>
            </v-btn>
          </div>

          <!-- Sound Picker Dialog -->
          <SoundSelectDialog
            v-model="showSoundPicker"
            :files="soundFiles"
            :currentValue="jsonData.userData.sound_effect"
            @select="onSoundSelected"
          />

          <div class="sound-controls" v-if="jsonData.userData.sound_effect">
            <div class="sound-control-row">
              <v-text-field
                v-model.number="jsonData.userData.sound_effect_duration"
                label="Sound Effect Duration"
                :suffix="'seconds'"
                density="compact"
                type="number"
                min="0"
                max="600"
                @input="onDataChange"
                outlined
                hide-details
              />
              <v-icon class="sound-control-icon">mdi-clock</v-icon>
            </div>
            <div class="sound-control-row">
              <v-slider
                v-model="jsonData.userData.sound_effect_volume"
                :min="1"
                :max="100"
                :step="1"
                hide-details
              />
              <v-icon class="sound-control-icon">mdi-volume-high</v-icon>
            </div>
          </div>
        </div>
        
        <div class="property-view__section">
          <div class="label-with-help" v-if="jsonData.userData">
            <label for="triggerDescription">Action Description</label>
            <HelpButton @click="openHelp('actionDescription')" />
          </div>
          <div class="editor-container" v-if="jsonData.userData">
            <textarea
                id="triggerDescription"
                v-model="jsonData.userData.description"
                @input="onDataChange"
                placeholder="Describe what possible happen on this action"
            ></textarea>
            <ExpandButton @click="showActionEditor = true" />
          </div>
        </div>

        <div class="property-view__section">
          <div class="label-with-help" v-if="jsonData.userData">
            <label for="systemPrompt">On Success</label>
            <HelpButton @click="openHelp('onSuccess')" />
          </div>
          <div class="editor-container" v-if="jsonData.userData">
            <textarea
                id="systemPrompt"
                v-model="jsonData.userData.system_prompt"
                @input="onDataChange"
                placeholder="Enter what happens on success of the action"
            ></textarea>
            <ExpandButton @click="showSuccessEditor = true" />
          </div>
        </div>

        <div class="field-group">
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

        <div class="field-group">
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
  import { mapGetters, mapActions } from 'vuex';
  import { MessageTypes, ShapeTypes } from '../../public/shared/SharedConstants.js';
  import ExtendedHelpDialog from '@/components/ExtendedHelpDialog.vue';
  import JinjaEditorDialog from '@/components/JinjaEditorDialog.vue';
  import SoundSelectDialog from '@/components/SoundSelectDialog.vue';
  import HelpButton from '@/components/HelpButton.vue';
  import ExpandButton from '@/components/ExpandButton.vue';
  import "codemirror/theme/material-darker.css";

  export default {
    name: 'PropertyView',
    components: { ExtendedHelpDialog, JinjaEditorDialog, SoundSelectDialog, HelpButton, ExpandButton },
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
        isInitializing: false, // Flag to prevent watchers from firing during initial data load
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
            title: 'Action Name',
            text: `<strong>The Unique Identifier for this Action</strong><br><br>
            Use descriptive names like <code>open_door</code> or <code>take_key</code>. This name is used internally and helps you organize your game logic.<br><br>
            <strong>🎯 AI Matching Importance:</strong><br>
            A well-chosen, descriptive name also helps the AI match this action with player input more accurately. The clearer and more specific the name, the better the AI can identify and execute the correct action when the player expresses their intent.<br><br>
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
            text: 'A sound effect that plays when this action activates. Choose a sound that matches the action, like a door opening, footsteps, or an item pickup. The sound provides audio feedback to enhance player immersion.'
          },
          actionDescription: {
            title: 'Action Description',
            text: `<p>Describe what the player wants to do. The AI uses this text to match player input against available actions.</p>

<p><strong>How it works:</strong></p>
<ul>
  <li>When a player types something, the AI compares it to all action descriptions</li>
  <li>If there's a match, this action executes</li>
  <li>Better descriptions = more accurate recognition</li>
</ul>

<p><strong>Good examples:</strong></p>
<ul>
  <li><em>"open the wooden door"</em></li>
  <li><em>"take the rusty key from the table"</em></li>
  <li><em>"examine the old chest in the corner"</em></li>
  <li><em>"talk to the bartender"</em></li>
</ul>

<p><strong>Tips:</strong></p>
<ul>
  <li>Be specific about the object and action</li>
  <li>Use natural language the player might type</li>
  <li>Include context if it helps (location, appearance)</li>
</ul>`
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
            Actions are executed when the action activates successfully. Use this to modify the game state and update the player's inventory. Enter one action per line.<br><br>
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
      ...mapActions('model', ['updateTrigger']),
      
      /**
       * Called when data is loaded/synced (initial load or programmatic update).
       * Sends data to the canvas iframe.
       */
      onDataLoad() { 
        this.jsonData.text = this.jsonData?.text?.replace(/[^a-zA-Z0-9_-]/g, '');
        var data = JSON.parse(JSON.stringify( this.jsonData ));
        window.postMessage({ type: MessageTypes.V2C_SET_SHAPE_DATA, data: data }, '*');
      },

      /**
       * Called only when data has actually changed by user interaction.
       * Sends data to canvas AND updates the Model Store.
       * TriggerLabels are stored as part of their parent StateShape in model.js.
       */
      onDataChange() {
        this.onDataLoad(); // Sync with canvas
        if (this.isInitializing) return;
        
        // Guard: Skip if no valid trigger is selected (e.g., after unselect)
        if (!this.jsonData?.id) return;
        
        // Update the trigger in the Model Store
        var data = JSON.parse(JSON.stringify(this.jsonData));
        this.updateTrigger(data);
      },

      onVolumeChange() {
        if(this.jsonData?.userData){
          const volume = this.jsonData.userData.sound_effect_volume || 100;
          SoundManager.setVolume(volume);
          this.onDataLoad();
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
          const duration = this.jsonData.userData.sound_effect_duration || null;
          SoundManager.playSound(this.jsonData.userData.sound_effect, volume, duration);
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
          this.onDataLoad(); // Always sync with canvas
          if (!this.isInitializing) {
            this.onDataChange();
          }
      },
      "jsonData.userData.sound_effect_volume"() {
        if (!this.isInitializing) {
          this.onVolumeChange();
        }
      },
      "jsonData.userData.description"() {
          this.onDataLoad(); // Always sync with canvas
          if (!this.isInitializing) {
            this.onDataChange();
          }
      },
      "jsonData.userData.sound_effect_duration"() {
          this.onDataLoad(); // Always sync with canvas
          if (!this.isInitializing) {
            this.onDataChange();
          }
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
            if (message.event === MessageTypes.C2V_SELECT && message.type === ShapeTypes.TRIGGER_LABEL) {
                SoundManager.stopCurrentSound()
                // Set flag to prevent watchers from firing during initial data load
                this.isInitializing = true;
                this.jsonData = message.data
                this.jsonData.userData.sound_effect_volume ??= 100;
                // 0 is allowed as well
                if (this.jsonData.userData.sound_effect_duration === null) {
                    this.jsonData.userData.sound_effect_duration = 2;
                }
                // Use nextTick to ensure all watchers have fired before clearing the flag
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
  ::v-deep .v-input__details { display: none; }

  .property-view {
    height: 100%;
    overflow-y: auto;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
  }

  /* Override for labels inside label-with-help */
  .label-with-help label {
    display: inline-block !important;
  }

  .property-view textarea {
    overflow-y: auto;
  }

  /* Sections that can grow but have a minimum height to prevent squashing */
  .property-view__section {
    flex: 1;
    display: flex;
    flex-direction: column;
  }

  /* Textareas in flex containers */
  .editor-container {
    flex: 1;
    display: flex;
    flex-direction: column;
  }

  .editor-container textarea {
    flex: 1;
    resize: none;
  }

  .sound-selection {
    display: flex;
    align-items: flex-start;
  }

  .sound-display {
    flex: 1;
    display: flex;
    align-items: center;
    cursor: pointer;
  }

  .sound-display .sound-icon {
    flex-shrink: 0;
  }

  .sound-display .sound-name {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .sound-display .browse-icon {
    flex-shrink: 0;
  }

  .sound-selection :deep(.v-select) {
    flex: 1;
  }

  .sound-control-row :deep(.v-text-field),
  .sound-control-row :deep(.v-slider) {
    flex: 1;
  }

  .sound-controls {
    display: flex;
    flex-direction: column;
  }

  .sound-control-row {
    display: flex;
    align-items: center;
  }

  .sound-control-icon {
    flex-shrink: 0;
  }

  :deep(.v-slider) {
    margin-inline: 0;
  }

  /* Editor Container with Expand Button */
  .editor-container {
    position: relative;
  }

  /* Field Group Container */
  .field-group {
    display: flex;
    flex-direction: column;
  }

  /* Label with Help Icon */
  .label-with-help {
    display: inline-flex;
    align-items: center;
  }

  .label-with-help label {
    display: inline-block;
  }
</style>
  