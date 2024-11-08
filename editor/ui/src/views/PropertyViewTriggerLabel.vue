<template>
    <div class="property-view"  v-if="jsonData.type === 'TriggerLabel'">
        <h3>Action</h3>
        <input
            id="stateName"
            type="text"
            lable="Name"
            v-model="jsonData.text"
            @input="onDataChange"
        />

        <!-- Sound ComboBox and Play Button -->
        <div class="sound-selection">
          <v-select
            v-model="jsonData.userData.sound_effect"
            :items="soundFiles"
            label="Sound Effect"
            density="compact"
            outlined
          ></v-select>
          <v-btn icon size="small" @click="playSelectedSound">
            <v-icon size="small">mdi-play</v-icon>
          </v-btn>
        </div>

        <div style="flex:1;display:flex;flex-direction: column;">
          <label v-if="jsonData.userData"  for="triggerDescription">Action Description</label>
          <textarea
              style="flex:1"
              v-if="jsonData.userData" 
              id="triggerDescription"
              v-model="jsonData.userData.description"
              @input="onDataChange"
              placeholder="Describe what possible happen on this action"
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
          text: "",
          userData: {
            system_prompt: '',
            actions: [], 
            conditions: [], 
            sound_effect: '',
            description: '',
          },
        },
        conditionsText: '',
        actionsText: '',
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
            var data = JSON.parse(JSON.stringify( this.jsonData ));
            this.draw2dFrame.postMessage({ type: 'setShapeData', data: data },'*');
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
          SoundManager.playSound(this.jsonData.userData.sound_effect);
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
      "jsonData.userData.description"() {
          this.onDataChange();
      },
    },
    mounted() {
        // Event listener for messages from the iframe
        window.addEventListener('message', (event) => {
            if (event.origin !== window.location.origin) return;
            const message = event.data;
            if (message.event === 'onSelect' && message.type == "TriggerLabel") {
                this.jsonData = message.data
            }
            else if (message.event === 'onUnselect') {
                this.jsonData = {}
            }
        });
    }
  };
  </script>
  
  <style scoped>
.property-view {
    max-height: 100%;
    overflow-y: auto;
    height: 100%;
    overflow-y: auto; 
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
  