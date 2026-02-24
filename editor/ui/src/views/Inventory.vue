<template>
  <div class="inventory-container">
    <!-- 8-Bit Retro Header -->
    <div class="inventory-header">
      <div class="inventory-header__title">
        <span>GAME INVENTORY</span>
        <HelpButton @click="showHelp = true" />
      </div>
    </div>

    <!-- Combined Input + List Table -->
    <div class="inventory-list">
      <v-table density="compact">
        <tbody>
          <!-- Input Row (First Row) -->
          <tr class="input-row">
            <td>
              <v-text-field
                ref="nameInput"
                v-model="newItem.key"
                placeholder="item_name"
                outlined
                dense
                hide-details
                @keyup.enter="handleEnter"
              ></v-text-field>
            </td>
            <td>
              <v-text-field
                v-model="newItem.value"
                placeholder="value"
                outlined
                dense
                hide-details
                @keyup.enter="handleEnter"
              ></v-text-field>
            </td>
            <td>
              <v-select
                v-model="newItem.type"
                :items="['string', 'boolean', 'integer']"
                outlined
                dense
                hide-details
              ></v-select>
            </td>
            <td>
              <RetroActionButton @click="addItem" variant="success" :disabled="!canAddItem">
                +
              </RetroActionButton>
            </td>
          </tr>
          
          <!-- Inventory Items -->
          <tr v-for="(item, index) in inventorySorted" :key="item.key">
            <td>{{ item.key }}</td>
            <td>
              <v-text-field
                v-model="item.value"
                :type="item.type === 'integer' ? 'number' : 'text'"
                @change="updateItem(item, index)"
                outlined
                density="compact"
                hide-details
              ></v-text-field>
            </td>
            <td>
              <v-select
                v-model="item.type"
                :items="['string', 'boolean', 'integer']"
                @change="updateItem(item, index)"
                outlined
                density="compact"
                hide-details
              ></v-select>
            </td>
            <td>
              <RetroActionButton @click="removeItem(item.key)" variant="danger">
                X
              </RetroActionButton>
            </td>
          </tr>
        </tbody>
      </v-table>
    </div>

    <!-- Extended Help Dialog -->
    <ExtendedHelpDialog
      v-model="showHelp"
      title="Game Inventory"
      :helpText="helpContent"
    />

    <!-- 8-Bit Toast Notification -->
    <transition name="toast-slide">
      <div v-if="showToast" class="toast-notification" :class="toastType">
        {{ toastMessage }}
      </div>
    </transition>
  </div>
</template>


<script>
import { mapGetters, mapActions } from 'vuex';
import ExtendedHelpDialog from '../components/ExtendedHelpDialog.vue';
import HelpButton from '../components/HelpButton.vue';
import RetroActionButton from '../components/RetroActionButton.vue';

export default {
  name: 'InventoryView',
  components: {
    ExtendedHelpDialog,
    HelpButton,
    RetroActionButton
  },
  data() {
    return {
      showHelp: false,
      helpContent: `
<p>Store game state variables that persist across states:</p>
<ul>
  <li><strong>Item counters</strong> - coins, eggs, etc.</li>
  <li><strong>Discovery flags</strong> - discovered_room, has_key</li>
  <li><strong>Player state</strong> - health, level, equipped items</li>
  <li><strong>Quest progress</strong> - door_closed, window_open</li>
</ul>
<p>Use these variables in your Jinja2 templates to create dynamic gameplay!</p>
      `,
      newItem: { key: '', value: '', type: 'string' },
      showToast: false,
      toastMessage: '',
      toastType: 'toast-success',
    };
  },
  computed: {
    ...mapGetters('config', ['inventory']),
    inventorySorted() {
      // Return inventory items sorted by key
      return [...(this.inventory || [])].sort((a, b) =>
        a.key.localeCompare(b.key)
      );
    },
    canAddItem() {
      return this.newItem.key.trim() !== '' && this.newItem.value !== '';
    },
  },
  mounted() {
    // Focus name input when component mounts
    this.$nextTick(() => {
      this.focusNameInput();
    });
  },
  methods: {
    ...mapActions('config', ['setInventory', 'addInventoryItem', 'removeInventoryItem', 'updateInventoryItem']),
    
    focusNameInput() {
      if (this.$refs.nameInput) {
        // Vuetify v-text-field: access the internal input element
        const input = this.$refs.nameInput.$el?.querySelector('input');
        if (input) {
          input.focus();
        }
      }
    },
    
    handleEnter() {
      if (this.canAddItem) {
        this.addItem();
      }
    },
    
    addItem() {
      if (this.newItem.key && this.newItem.value !== undefined) {
        // Convert value to the appropriate type
        const item = {
          key: this.newItem.key,
          value: this.convertType(this.newItem.value, this.newItem.type),
          type: this.newItem.type
        };

        // Add the new item via Vuex action
        this.addInventoryItem(item);
        
        // Show success toast notification
        this.toastMessage = 'Inventory item created!';
        this.toastType = 'toast-success';
        this.showToast = true;
        setTimeout(() => {
          this.showToast = false;
        }, 2000);
        
        // Reset the form
        this.newItem = { key: '', value: '', type: 'string' };
        
        // Re-focus the name input for quick entry of next item
        this.$nextTick(() => {
          this.focusNameInput();
        });
      }
    },

    updateItem(item, index) {
      // Convert value based on type
      const updatedItem = {
        ...item,
        value: this.convertType(item.value, item.type)
      };
      
      // Update via Vuex action
      this.updateInventoryItem({ index, item: updatedItem });
    },

    removeItem(key) {
      // Find index of item with key
      const index = this.inventory.findIndex(item => item.key === key);
      if (index !== -1) {
        // Remove via Vuex action
        this.removeInventoryItem(index);
        
        // Show error toast notification
        this.toastMessage = 'Inventory item removed!';
        this.toastType = 'toast-error';
        this.showToast = true;
        setTimeout(() => {
          this.showToast = false;
        }, 2000);
      }
    },

    convertType(value, type) {
      switch (type) {
        case 'boolean':
          return value === 'true' || value === true;
        case 'integer':
          return parseInt(value) || 0;
        default:
          return String(value);
      }
    },
  },
};
</script>

<style scoped>
.inventory-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--game-bg-secondary);
  padding: 0;
  overflow: hidden; /* NUR .inventory-list soll scrollen, nicht der Container */
  box-sizing: border-box;
}

/* 8-Bit Retro Header */
.inventory-header {
  padding: var(--screen-wide-header-padding-y, var(--game-spacing-lg)) var(--game-spacing-lg);
  background: linear-gradient(135deg, var(--game-bg-tertiary) 0%, #1a1a2e 100%);
  border-bottom: 3px solid var(--game-accent-primary);
  border-top: 2px solid var(--game-accent-secondary);
  box-shadow: inset 0 -2px 0 rgba(0, 0, 0, 0.3);
}

.inventory-header__title {
  display: flex;
  align-items: center;
  gap: var(--screen-wide-header-gap, var(--game-spacing-md));
  color: var(--game-accent-secondary);
  font-family: var(--game-font-family-retro);
  font-size: var(--screen-wide-header-font-size, 16px);
  letter-spacing: var(--screen-wide-header-letter-spacing, 2px);
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    filter: drop-shadow(0 0 8px var(--game-accent-secondary));
  }
  50% {
    transform: scale(1.05);
    filter: drop-shadow(0 0 12px var(--game-accent-secondary));
  }
}

.inventory-header__info {
  color: var(--game-text-secondary);
  font-size: var(--screen-wide-header-info-size, 24px);
  cursor: pointer;
  transition: all var(--game-transition-fast);
}

.inventory-header__info:hover {
  color: var(--game-accent-secondary);
  filter: drop-shadow(0 0 8px var(--game-accent-secondary));
  transform: scale(1.1);
}

/* Responsive header for laptop screens (60% height) */
@media (max-width: 1439px) {
  .inventory-header {
    padding: var(--screen-medium-header-padding-y) var(--game-spacing-lg);
  }
  
  .inventory-header__title {
    font-size: var(--screen-medium-header-font-size);
    gap: var(--screen-medium-header-gap);
    letter-spacing: var(--screen-medium-header-letter-spacing);
  }
  
  .inventory-header__info {
    font-size: var(--screen-medium-header-info-size);
  }
}

/* Responsive header for small screens */
@media (max-width: 1023px) {
  .inventory-header {
    padding: var(--screen-small-header-padding-y) var(--game-spacing-md);
  }
  
  .inventory-header__title {
    font-size: var(--screen-small-header-font-size);
    gap: var(--screen-small-header-gap);
    letter-spacing: var(--screen-small-header-letter-spacing);
  }
  
  .inventory-header__info {
    font-size: var(--screen-small-header-info-size);
  }
}

/* Input Row (First Row in Table) - Hervorgehoben */
.input-row {
  background: var(--game-bg-tertiary) !important;
  border-bottom: 3px solid var(--game-accent-primary) !important;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3) !important;
}

.input-row:hover {
  background: var(--game-bg-tertiary) !important;
}

.input-row td {
  padding: 12px 8px !important;
}


.inventory-list {
  overflow-y: auto;
  flex: 1;
  min-height: 0; /* WICHTIG: Erlaubt flex-item zu schrumpfen */
  padding: var(--game-spacing-sm);
  background: var(--game-bg-primary);
}

.inventory-list :deep(.v-table) {
  background: transparent;
  color: var(--game-text-primary);
}

.inventory-list :deep(tbody tr) {
  border-bottom: 1px solid var(--game-border-color);
  transition: all var(--game-transition-fast);
}

.inventory-list :deep(tbody tr:hover) {
  background: var(--game-input-hover);
}

.inventory-list :deep(td) {
  color: var(--game-text-primary);
  font-family: var(--game-font-family-mono);
  font-size: 14px;
  padding: 8px;
}

.inventory-list :deep(td:first-child) {
  color: var(--game-accent-secondary);
}

.prompt-field {
  flex: 1;
}

.prompt-field:focus {
  border-color: var(--game-border-highlight);
}

.inventory-list :deep(.v-field--focused) {
  border-color: var(--game-accent-primary);
}

.inventory-list :deep(.v-field__input) {
  color: var(--game-text-primary);
  font-size: 13px;
  padding: 4px 8px;
  min-height: 32px;
}

/* Inventory List Scrollbar */
.inventory-list::-webkit-scrollbar {
  width: 12px;
}

.inventory-list::-webkit-scrollbar-track {
  background: var(--game-bg-tertiary);
  border-radius: var(--game-radius-sm);
}

.inventory-list::-webkit-scrollbar-thumb {
  background: var(--game-accent-primary);
  border-radius: var(--game-radius-sm);
  border: 2px solid var(--game-bg-tertiary);
}

.inventory-list::-webkit-scrollbar-thumb:hover {
  background: var(--game-accent-tertiary);
  box-shadow: 0 0 8px var(--game-accent-primary);
}

/* 8-Bit Toast Notification */
.toast-notification {
  position: fixed;
  top: 80px;
  right: 20px;
  color: white;
  padding: 16px 24px;
  border-radius: 0;
  border: 3px solid black;
  z-index: 9999;
  font-family: var(--game-font-family-retro);
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
}

/* Success Toast (Green) */
.toast-notification.toast-success {
  background: var(--game-success);
  box-shadow: inset -4px -4px 0px 0px #1e7e34,
              0 8px 16px rgba(0, 0, 0, 0.4);
}

/* Error Toast (Red/Pink) */
.toast-notification.toast-error {
  background: var(--game-accent-primary);
  box-shadow: inset -4px -4px 0px 0px #8c2022,
              0 8px 16px rgba(0, 0, 0, 0.4);
}

/* Toast Slide Animation */
.toast-slide-enter-active {
  animation: toast-slide-in 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

.toast-slide-leave-active {
  animation: toast-slide-out 0.3s ease-in;
}

@keyframes toast-slide-in {
  0% {
    transform: translateX(400px);
    opacity: 0;
  }
  100% {
    transform: translateX(0);
    opacity: 1;
  }
}

@keyframes toast-slide-out {
  0% {
    transform: translateX(0);
    opacity: 1;
  }
  100% {
    transform: translateX(400px);
    opacity: 0;
  }
}
</style>
