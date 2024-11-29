<template>
    <div class="property-view" v-if="jsonData.type === 'StateShape'">

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
            v-model="jsonData.userData.ambient_sound_volume"
            :min="1"
            :max="100"
            :step="1"
            append-icon="mdi-volume-high"
          />
        </div>
        
        <label v-if="jsonData.userData"  for="systemPrompt">Sceen Description</label>
        <Codemirror
            v-if="jsonData.userData" 
            class="code-editor"
            v-model:value="jsonData.userData.system_prompt"
            :options="cmOptions"
            placeholder="test placeholder"
            @change="onDataChange"
        />

    </div>
</template>
  
<script>
  import SoundManager from '@/utils/SoundManager'
  import { mapGetters } from 'vuex';

  import Codemirror from "codemirror-editor-vue3";
  import "codemirror/addon/display/placeholder.js";
  import "codemirror/mode/jinja2/jinja2.js";
  import "codemirror/addon/display/placeholder.js";
  import "codemirror/theme/juejin.css";
  import "codemirror/theme/material-darker.css";

  export default {
    name: 'PropertyView',
    components: { Codemirror },
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
            var data = JSON.parse(JSON.stringify( this.jsonData ));
            this.draw2dFrame.postMessage({ type: 'setShapeData', data: data },'*');
        }
      },

      onVolumeChange() {
        if(this.jsonData?.userData){
          const volume = this.jsonData.userData.ambient_sound_volume || 100;
          SoundManager.setVolume(volume);
          this.onDataChange();
        }
      },

      async playSelectedSound() {
        if (this.jsonData.userData.ambient_sound) {
          const volume = this.jsonData.userData.ambient_sound_volume || 100;
          SoundManager.playSound(this.jsonData.userData.ambient_sound, volume);
        }
      },
    },

    mounted() {
        // Event listener for messages from the iframe
        window.addEventListener('message', (event) => {
            if (event.origin !== window.location.origin) return;
            const message = event.data;
            if (message.event === 'onSelect' && message.type == "StateShape") {
                SoundManager.stopCurrentSound()
                this.jsonData = message.data;
                if (!this.jsonData.userData.ambient_sound_volume) {
                  this.jsonData.userData.ambient_sound_volume = 100;
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
  ::v-deep .v-input__details {
    display: none;
  }

  .property-view {
    font-size: small;
    height: 100%;
    overflow-y: auto;
    padding: 10px;
    box-sizing: border-box; 
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  
.property-view label {
  display: block;
  margin: 0px;
  font-size:70%;
}

.property-view input {
  width: 100%;
  padding: 5px;
  border-radius: 4px;
}

.sound-selection {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.v-combobox {
  flex: 1; 
}


.code-editor >>> .CodeMirror {
  font-size: 16px; /* Hier kannst du die Schriftgröße anpassen */
  font-family: 'Roboto', Arial, Helvetica, sans-serif !important;
}

.code-editor >>> .CodeMirror-gutters {
  display: none !important; /* Versteckt den gesamten Gutter-Bereich */
}
  </style>
  