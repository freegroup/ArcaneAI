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
              <ThemedActionButton @click="addItem" variant="success" :disabled="!canAddItem">
                +
              </ThemedActionButton>
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
              <ThemedActionButton @click="removeItem(item.key)" variant="danger">
                X
              </ThemedActionButton>
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
import ThemedActionButton from '../components/ThemedActionButton.vue';

export default {
  name: 'InventoryView',
  components: {
    ExtendedHelpDialog,
    HelpButton,
    ThemedActionButton
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
  flex: 1;
  overflow: hidden;
  box-sizing: border-box;
}

/* 8-Bit Retro Header */
.inventory-header {
}

.inventory-header__title {
  display: flex;
  align-items: center;
}

.inventory-list {
  overflow-y: auto;
  flex: 1;
}

/* Toast Notification */
.toast-notification {
  position: fixed;
  z-index: 9999;
}

/* Toast Slide Animation */
.toast-slide-enter-active {
  animation: toast-slide-in 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

.toast-slide-leave-active {
  animation: toast-slide-out 0.3s ease-in;
}

@keyframes toast-slide-in {
  0% { transform: translateX(400px); opacity: 0; }
  100% { transform: translateX(0); opacity: 1; }
}

@keyframes toast-slide-out {
  0% { transform: translateX(0); opacity: 1; }
  100% { transform: translateX(400px); opacity: 0; }
}
</style>
