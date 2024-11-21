<template>
    <div class="property-view"  v-if="jsonData.type === 'TriggerConnection'">
        <h3>Action</h3>
        <input
            id="triggerName"
            type="text"
            label="Name"
            v-model="jsonData.name"
            @input="onDataChange"
        />

        <!-- Sound ComboBox and Play Button -->
        <div class="sound-selection">
          <v-select
            v-model="jsonData.userData.sound_effect"
            :items="soundFiles"
            label="Sound Effect"
            density="compact"
            :items-per-page="1000"
            :list-props="{maxWidth:'350px', minWidth: '350px'}"
            outlined
          ></v-select>
          <v-btn icon size="small" @click="playSelectedSound">
            <v-icon size="small">mdi-play</v-icon>
          </v-btn>
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
        
        <div style="flex:1;display:flex;flex-direction: column;">
          <label v-if="jsonData.userData"  for="triggerDescription">Action Description</label>
          <textarea
              style="flex:1"
              id="triggerDescription"
              type="text"
              placeholder="Describe what possible happen on this action"
              v-model="jsonData.userData.description"
              @input="onDataChange"
          ></textarea>
        </div>

        <div style="flex:1;display:flex;flex-direction: column;">
          <label v-if="jsonData.userData"  for="systemPrompt">On Success</label>
          <textarea
              style="flex:1"
              v-if="jsonData.userData" 
              id="systemPrompt"
              v-model="jsonData.userData.system_prompt"
              @input="onDataChange"
              placeholder="Enter what happens on success of the action"
          ></textarea>
          </div>

        <!-- Textarea for Conditions -->
        <div>
          <label for="conditions">Conditions</label>
          <textarea
            id="conditions"
            v-model="conditionsText"
            @input="updateConditions"
            placeholder="Enter each condition on a new line"
          ></textarea>
        </div>

        <div>
          <label for="actions">Actions</label>
          <textarea
            id="actions"
            v-model="actionsText"
            @input="updateActions"
            placeholder="Enter each action on a new line"
          ></textarea>
        </div>

    </div>
  </template>
  
<script>
  import SoundManager from '@/utils/SoundManager'

  import { mapGetters } from 'vuex';

  export default {
    name: 'PropertyView',
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
            actions: [], 
            conditions: [],
            sound_effect: '',
            sound_effect_volume: 100,
            description: '',
          },
          conditionsText: '',
          actionsText: '',
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
        this.jsonData.name = this.jsonData?.name?.replace(/[^a-zA-Z0-9_-]/g, '');
        if (this.draw2dFrame ) {
            var data = JSON.parse(JSON.stringify( this.jsonData ));
            this.draw2dFrame.postMessage({ type: 'setShapeData', data: data },'*');
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
      async playSelectedSound() {
        if (this.jsonData.userData.sound_effect) {
          const volume = this.jsonData.userData.sound_effect_volume || 100;
          SoundManager.playSound(this.jsonData.userData.sound_effect,volume);
        }
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
    },
    mounted() {
      // Event listener for messages from the iframe
      window.addEventListener('message', (event) => {
          if (event.origin !== window.location.origin) return;
          const message = event.data;
          if (message.event === 'onSelect' && message.type === "TriggerConnection") {
              SoundManager.stopCurrentSound()
              this.jsonData = message.data
              if (!this.jsonData.userData.sound_effect_volume) {
                  this.jsonData.userData.sound_effect_volume = 100;
              }
          }
          else if (message.event === 'onUnselect') {
              SoundManager.stopCurrentSound()
              this.jsonData = {}
          }
      });
    }
  };
  </script>
  
  <style scoped>
  .property-view {
    height: 100%;
    overflow-y: auto; /* Enables vertical scrolling if content exceeds height */
    padding: 10px;
    background-color: #fafafa;
    border-left: 1px solid #ddd;
    box-sizing: border-box; 
    display: flex;
    flex-direction: column;
    gap: 5px;
  }
  

.property-view h3 {
  margin-top: 0;
}

.property-view label {
  display: block;
  margin: 0px;
  font-size:70%;
}

.property-view input {
  width: 100%;
  padding: 5px;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.property-view textarea {
  width: 100%;
  padding: 5px;
  border: 1px solid #ccc;
  border-radius: 4px;
  resize: vertical; /* Allows vertical resizing only */
  background-color: #f9f9f9;
  flex: 1;
}


.sound-selection {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.v-combobox {
  flex: 1; 
}
  </style>
  