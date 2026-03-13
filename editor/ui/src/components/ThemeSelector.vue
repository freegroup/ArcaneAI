<template>
  <div class="theme-selector" v-click-outside="close">
    <button ref="trigger" class="theme-selector__trigger" @click="toggle">
      <span class="theme-selector__label">{{ currentLabel }}</span>
      <span class="theme-selector__arrow" :class="{ 'theme-selector__arrow--open': open }">&#9662;</span>
    </button>
    <Teleport to="body">
      <transition name="theme-selector-dropdown">
        <ul
          v-if="open"
          ref="dropdown"
          class="theme-selector__dropdown"
          :style="dropdownStyle"
        >
          <li
            v-for="theme in availableThemes"
            :key="theme.id"
            class="theme-selector__option"
            :class="{ 'theme-selector__option--active': theme.id === currentTheme }"
            @click="selectTheme(theme.id)"
          >
            {{ theme.label }}
          </li>
        </ul>
      </transition>
    </Teleport>
  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex';

export default {
  name: 'ThemeSelector',
  directives: {
    'click-outside': {
      mounted(el, binding) {
        el._clickOutside = (e) => {
          if (!el.contains(e.target) && !e.target.closest('.theme-selector__dropdown')) {
            binding.value();
          }
        };
        document.addEventListener('click', el._clickOutside);
      },
      unmounted(el) {
        document.removeEventListener('click', el._clickOutside);
      },
    },
  },
  data() {
    return {
      open: false,
      dropdownStyle: {},
    };
  },
  computed: {
    ...mapGetters('settings', ['currentTheme', 'availableThemes']),
    currentLabel() {
      const t = this.availableThemes.find(t => t.id === this.currentTheme);
      return t ? t.label : 'Theme';
    },
  },
  methods: {
    ...mapActions('settings', ['setTheme']),
    toggle() {
      this.open = !this.open;
      if (this.open) {
        this.$nextTick(() => this.positionDropdown());
      }
    },
    close() {
      this.open = false;
    },
    selectTheme(id) {
      this.setTheme(id);
      this.open = false;
    },
    positionDropdown() {
      const trigger = this.$refs.trigger;
      if (!trigger) return;
      const rect = trigger.getBoundingClientRect();
      this.dropdownStyle = {
        position: 'fixed',
        top: `${rect.bottom + 4}px`,
        right: `${window.innerWidth - rect.right}px`,
        zIndex: 10000,
      };
    },
  },
};
</script>

<style scoped>
/* Structural only — visual styles in theme files (theme-selector.css) */
.theme-selector {
  display: inline-flex;
  align-items: center;
}

.theme-selector__trigger {
  display: inline-flex;
  align-items: center;
  cursor: pointer;
  box-sizing: border-box;
}
</style>

<style>
/* Dropdown is teleported to body — these must be global */
.theme-selector__dropdown {
  list-style: none;
  margin: 0;
  box-sizing: border-box;
}

.theme-selector__option {
  cursor: pointer;
  box-sizing: border-box;
  white-space: nowrap;
}

.theme-selector-dropdown-enter-active,
.theme-selector-dropdown-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.theme-selector-dropdown-enter-from,
.theme-selector-dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
