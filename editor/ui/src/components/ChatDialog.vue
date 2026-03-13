<template>
  <v-dialog v-model="dialogVisible" max-width="1100px" @click:outside="closeDialog">
    <v-card class="chat-dialog">
      <DialogHeader
        :title="`Chat from: ${currentState || stateName}`"
        @close="closeDialog"
      />

      <v-card-text class="chat-container">
        <!-- Inventory Panel (Left) -->
        <div class="inventory-panel">
          <div class="inventory-header">📦 Inventory</div>
          <div class="inventory-list" ref="inventoryList">
            <div v-for="item in inventoryItems" :key="item.key" class="inventory-item">
              <span class="item-key">{{ item.key }}</span>
              <!-- Boolean: Checkbox -->
              <input 
                v-if="item.type === 'boolean'"
                type="checkbox"
                :checked="item.value"
                @change="updateInventoryItem(item.key, $event.target.checked)"
                class="item-checkbox"
              />
              <!-- Integer: Number input -->
              <input 
                v-else-if="item.type === 'integer'"
                type="number"
                :value="item.value"
                @change="updateInventoryItem(item.key, parseInt($event.target.value) || 0)"
                class="item-number"
              />
              <!-- String: Text input -->
              <input 
                v-else
                type="text"
                :value="item.value"
                @change="updateInventoryItem(item.key, $event.target.value)"
                class="item-text"
              />
            </div>
            <div v-if="inventoryItems.length === 0" class="inventory-empty">
              No inventory items
            </div>
          </div>
        </div>
        
        <!-- Chat messages area (Right) -->
        <div class="messages-area" ref="messagesArea">
          <!-- Error message -->
          <div v-if="error" class="message system-message error-message">
            <div class="message-content">⚠ {{ error }}</div>
          </div>
          
          <!-- Typing indicator while connecting -->
          <div v-if="connecting" class="message ai-message">
            <div class="message-content">
              <span class="typing-indicator">
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
              </span>
            </div>
          </div>
          
          <!-- Chat messages -->
          <div v-for="(msg, index) in messages" :key="index" 
               :class="['message', msg.role === 'user' ? 'user-message' : (msg.role === 'system' ? 'system-message' : 'ai-message')]">
            <div class="message-content">{{ msg.content }}</div>
          </div>
          
          <!-- Typing indicator while waiting for response -->
          <div v-if="sending" class="message ai-message">
            <div class="message-content">
              <span class="typing-indicator">
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
              </span>
            </div>
          </div>
        </div>
      </v-card-text>
      
      <v-card-actions class="chat-actions">
        <div class="input-wrapper">
          <input
            ref="chatInput"
            type="text"
            v-model="inputMessage"
            placeholder="Type your message..."
            :disabled="sending || connecting"
            @keyup.enter="sendMessage"
            class="chat-input"
          />
          <ThemedButton 
            variant="proceed"
            :disabled="!inputMessage.trim() || connecting || sending"
            @click="sendMessage"
          >
            Send
          </ThemedButton>
        </div>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import axios from 'axios';
import { mapState, mapGetters } from 'vuex';
import DialogHeader from './DialogHeader.vue';
import ThemedButton from './ThemedButton.vue';

const API_BASE_URL = process.env.VUE_APP_API_BASE_URL || '';

export default {
  name: 'ChatDialog',
  components: { DialogHeader, ThemedButton },
  props: {
    modelValue: {
      type: Boolean,
      default: false
    },
    stateName: {
      type: String,
      default: ''
    }
  },
  emits: ['update:modelValue'],
  data() {
    return {
      messages: [],
      inputMessage: '',
      sending: false,
      connecting: false,
      error: null,
      currentState: '',
      inventoryItems: []  // Array of {key, value, type}
    };
  },
  computed: {
    ...mapState('model', ['states', 'connections']),
    ...mapGetters('config', ['gameConfig']),
    dialogVisible: {
      get() {
        return this.modelValue;
      },
      set(value) {
        this.$emit('update:modelValue', value);
      }
    }
  },
  watch: {
    modelValue(newVal) {
      if (newVal && this.stateName) {
        this.initializeChat();
      }
    }
  },
  methods: {
    async initializeChat() {
      this.messages = [];
      this.error = null;
      this.connecting = true;
      this.inventoryItems = [];
      
      try {
        // Build model_json from current Vue store state (may have unsaved changes)
        const modelJson = {
          states: this.states,
          connections: this.connections
        };
        
        // Build config_json from current Vue store state
        const configJson = this.gameConfig;
        
        // Initialize inventory from config (with types)
        if (configJson?.inventory) {
          this.inventoryItems = configJson.inventory.map(item => ({
            key: item.key,
            value: item.value,
            type: item.type || 'string'
          }));
        }
        
        // Set the active state in Developer Server with current in-memory model
        await axios.post(`${API_BASE_URL}/developer/setState`, {
          state_name: this.stateName,
          model_json: modelJson,
          config_json: configJson
        });
        
        // Get current status to show initial state info
        const statusResponse = await axios.get(`${API_BASE_URL}/developer/status`);
        const status = statusResponse.data;
        
        // Update current state for header
        this.currentState = status.current_state;
        
        // Update inventory values from server (keeps types from config)
        this.updateInventoryFromServer(status.inventory);
        
        // Add initial system message
        this.messages.push({
          role: 'assistant',
          content: `State: "${status.current_state}" - Ready to chat!`
        });
        
      } catch (err) {
        if (err.response?.status === 503) {
          this.error = 'Developer Server is not running. Start the game first.';
        } else {
          this.error = err.response?.data?.detail || 'Failed to connect to Developer Server';
        }
      } finally {
        this.connecting = false;
        this.scrollToBottom();
        this.focusInput();
      }
    },
    
    updateInventoryFromServer(serverInventory) {
      // Update inventory values from server while preserving types
      if (!serverInventory) return;
      
      for (const item of this.inventoryItems) {
        if (item.key in serverInventory) {
          item.value = serverInventory[item.key];
        }
      }
    },
    
    async updateInventoryItem(key, value) {
      // Update local state
      const item = this.inventoryItems.find(i => i.key === key);
      if (item) {
        item.value = value;
      }
      
      // Send update to server
      try {
        await axios.post(`${API_BASE_URL}/developer/setInventory`, {
          key: key,
          value: value
        });
      } catch (err) {
        console.error('Failed to update inventory:', err);
      }
    },
    
    async sendMessage() {
      if (!this.inputMessage.trim() || this.sending) return;
      
      const userMessage = this.inputMessage.trim();
      this.inputMessage = '';
      this.error = null;
      
      // Add user message to chat
      this.messages.push({
        role: 'user',
        content: userMessage
      });
      
      this.scrollToBottom();
      this.sending = true;
      
      try {
        const response = await axios.post(`${API_BASE_URL}/developer/chat`, {
          message: userMessage
        });
        
        // Add AI response
        this.messages.push({
          role: 'assistant',
          content: response.data.response
        });
        
        // If an action was executed, show it
        if (response.data.executed_action) {
          this.messages.push({
            role: 'system',
            content: `⚡ Action: ${response.data.executed_action}`
          });
        }
        
        // If state changed, add info message and update header
        if (response.data.current_state && response.data.current_state !== this.currentState) {
          this.messages.push({
            role: 'system',
            content: `→ State changed to: ${response.data.current_state}`
          });
          // Update header with new state
          this.currentState = response.data.current_state;
        }
        
        // Update inventory from server response
        if (response.data.inventory) {
          this.updateInventoryFromServer(response.data.inventory);
        }
        
      } catch (err) {
        this.error = err.response?.data?.detail || 'Failed to send message';
        // Remove the user message if sending failed
        this.messages.pop();
        this.inputMessage = userMessage;
      } finally {
        this.sending = false;
        this.scrollToBottom();
        this.focusInput();
      }
    },
    
    scrollToBottom() {
      this.$nextTick(() => {
        const area = this.$refs.messagesArea;
        if (area) {
          area.scrollTop = area.scrollHeight;
        }
      });
    },
    
    focusInput() {
      this.$nextTick(() => {
        if (this.$refs.chatInput && !this.sending && !this.connecting) {
          this.$refs.chatInput.focus();
        }
      });
    },
    
    closeDialog() {
      this.dialogVisible = false;
      this.messages = [];
      this.inputMessage = '';
      this.error = null;
      this.currentState = '';
      this.inventoryItems = [];
    }
  }
};
</script>

<style scoped>
.chat-container {
  padding: 0 !important;
  display: flex;
  flex-direction: row;
  overflow: hidden;
}

/* Inventory Panel */
.inventory-panel {
  display: flex;
  flex-direction: column;
}

.inventory-list {
  flex: 1;
  overflow-y: auto;
}

.inventory-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.item-key {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-checkbox {
  cursor: pointer;
}

.item-number {
  text-align: right;
}

.inventory-empty {
  font-style: italic;
  text-align: center;
}

/* Messages Area */
.messages-area {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  display: flex;
  flex-direction: column;
  scroll-behavior: smooth;
}

/* Message Styles */
.message {
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.user-message {
  align-self: flex-end;
}

.ai-message {
  align-self: flex-start;
}

.system-message {
  align-self: center;
}

/* Typing Indicator - Three Bouncing Dots */
.typing-indicator {
  display: inline-flex;
  align-items: center;
}

.typing-indicator .dot {
  animation: bounce 1.4s infinite ease-in-out both;
}

.typing-indicator .dot:nth-child(1) {
  animation-delay: -0.32s;
}

.typing-indicator .dot:nth-child(2) {
  animation-delay: -0.16s;
}

.typing-indicator .dot:nth-child(3) {
  animation-delay: 0s;
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: translateY(0);
  }
  40% {
    transform: translateY(-10px);
  }
}

/* Chat Actions */
.input-wrapper {
  display: flex;
  width: 100%;
}

.chat-input {
  flex: 1;
}

.chat-input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>