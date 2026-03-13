<template>
  <div class="dialog-header">
    <div class="dialog-header__content">
      <slot>
        <span v-if="icon" class="dialog-header__icon">{{ iconChar }}</span>
        <span v-if="title" class="dialog-header__title">{{ title }}</span>
      </slot>
    </div>
    <ThemedActionButton
      class="dialog-header__close"
      variant="danger"
      @click="$emit('close')"
      title="Close"
    >
      X
    </ThemedActionButton>
  </div>
</template>

<script>
import ThemedActionButton from './ThemedActionButton.vue';

export default {
  name: 'DialogHeader',
  components: { ThemedActionButton },
  emits: ['close'],
  props: {
    title: {
      type: String,
      default: ''
    },
    icon: {
      type: String,
      default: ''
    }
  },
  computed: {
    iconChar() {
      const iconMap = {
        'mdi-help-circle': '?',
        'mdi-code-braces': '{ }',
        'mdi-music-box': '♪',
        'mdi-map': '⌂',
        'mdi-gamepad-variant': '♠',
        'mdi-plus-box': '+',
        'mdi-information': 'i',
        'mdi-treasure-chest': '▣',
        'mdi-account-alert': '☺',
        'mdi-pencil': '✎'
      };
      return iconMap[this.icon] || '■';
    }
  }
};
</script>

<style scoped>
.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.dialog-header__content {
  display: flex;
  align-items: center;
  flex: 1;
}

.dialog-header__icon {
  min-width: 32px;
  text-align: center;
}
</style>
