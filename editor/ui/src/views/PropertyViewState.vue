<template>
    <div class="property-view" v-if="jsonData.type === 'StateShape'">
        <h3>Sceene</h3>
        <input
            id="stateName"
            type="text"
            v-model="jsonData.name"
            @input="onDataChange"
        />

        <!-- Ambient Sound ComboBox and Play Button -->
        <div class="sound-selection">
          <v-select
            v-model="jsonData.userData.ambient_sound"
            :items="soundFiles"
            density="compact"
            label="Ambient Sound"
            outlined
          ></v-select>
          
          <v-btn icon size="small" @click="playSelectedSound">
            <v-icon size="small">mdi-play</v-icon>
          </v-btn>
        </div>
    
        
        <label v-if="jsonData.userData"  for="systemPrompt">Sceen Description</label>
        <textarea
            v-if="jsonData.userData" 
            id="systemPrompt"
            v-model="jsonData.userData.system_prompt"
            @input="onDataChange"
            rows="5"
            placeholder="Enter detailed system instructions here..."
        ></textarea>

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
            ambient_sound: '',
          },
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
    },
    methods: {

      onDataChange() { 
        console.log(this.jsonData)
        this.jsonData.name = this.jsonData?.name?.replace(/[^a-zA-Z0-9]/g, '');
        if (this.draw2dFrame ) {
            var data = JSON.parse(JSON.stringify( this.jsonData ));
            this.draw2dFrame.postMessage({ type: 'setShapeData', data: data },'*');
        }
      },

      async playSelectedSound() {
        if (this.jsonData.userData.ambient_sound) {
          SoundManager.playSound(this.jsonData.userData.ambient_sound);
        }
      },
    },

    mounted() {
        // Event listener for messages from the iframe
        window.addEventListener('message', (event) => {
            if (event.origin !== window.location.origin) return;
            const message = event.data;
            if (message.event === 'onSelect' && message.type == "StateShape") {
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
    height: 100%;
    overflow-y: auto;
    padding: 10px;
    background-color: #fafafa;
    border-left: 1px solid #ddd;
    box-sizing: border-box; 
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  

  .property-view h3 {
  margin-top: 0;
}

.property-view label {
  display: block;
  margin: 10px 0 5px;
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
  