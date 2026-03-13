/**
 * Shared Constants for Canvas ↔ Vue Communication
 * 
 * This file uses UMD (Universal Module Definition) pattern to work in both:
 * - Browser global scope (for draw2d canvas code)
 * - ES6 modules (for Vue components)
 * 
 * Usage in Browser (canvas):
 *   <script src="./SharedConstants.js"></script>
 *   window.parent.postMessage({ type: MessageTypes.CANVAS_READY }, origin);
 * 
 * Usage in Vue:
 *   import { MessageTypes, ShapeTypes } from '../../public/shared/SharedConstants.js';
 *   if (message.type === MessageTypes.CANVAS_READY) { ... }
 */

/* eslint-disable no-undef */
(function (root, factory) {
  if (typeof define === 'function' && define.amd) {
    // AMD
    define([], factory);
  } else if (typeof module === 'object' && module.exports) {
    // Node/CommonJS
    const result = factory();
    module.exports = result;
    module.exports.MessageTypes = result.MessageTypes;
    module.exports.ShapeTypes = result.ShapeTypes;
  } else if (typeof exports === 'object') {
    // ES6 Module
    const result = factory();
    exports.MessageTypes = result.MessageTypes;
    exports.ShapeTypes = result.ShapeTypes;
  } else {
    // Browser global
    const result = factory();
    root.MessageTypes = result.MessageTypes;
    root.ShapeTypes = result.ShapeTypes;
  }
}(typeof self !== 'undefined' ? self : this, function () {

  // ====================================
  // Theme Helper - Read CSS Custom Properties
  // ====================================
  const root = typeof self !== 'undefined' ? self : this;
  root.getVar = (name, fallback) =>
      getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback;

  // ====================================
  // Shape Types - Shape Identifiers
  // ====================================
  const ShapeTypes = {
    STATE: 'StateShape',
    TRIGGER_LABEL: 'TriggerLabel',
    TRIGGER_CONNECTION: 'TriggerConnection',
  };
  
  // ====================================
  // Message Types - Communication Events
  // ====================================
  // 
  // Naming Convention:
  //   C2V_* = Canvas-to-Vue (Canvas sends, Vue receives)
  //   V2C_* = Vue-to-Canvas (Vue sends, Canvas receives)
  //
  // Value Convention:
  //   'c2v:*' = Canvas-to-Vue message values
  //   'v2c:*' = Vue-to-Canvas message values
  //   This allows easy filtering: message.type.startsWith('c2v:') or 'v2c:'
  //
  const MessageTypes = {
    // C2V: Canvas → Vue Messages
    C2V_CANVAS_READY: 'c2v:canvasReady',
    C2V_DOCUMENT_UPDATED: 'c2v:documentUpdated',
    C2V_ELEMENT_UPDATED: 'c2v:elementUpdated',
    C2V_SELECT: 'c2v:select',
    C2V_UNSELECT: 'c2v:unselect',
    C2V_CCM: 'c2v:ccm',  // Canvas notifies Vue about content changes (for ContentChangeManager)
    C2V_OPEN_IMPORT_DIALOG: 'c2v:openImportDialog',  // Canvas requests Vue to open Import State dialog
    C2V_CHAT_FROM_HERE: 'c2v:chatFromHere',  // Canvas requests Vue to open chat dialog from specific state
    C2V_FOCUS_PROPERTY: 'c2v:focusProperty',  // Canvas requests Vue to focus a property field (e.g., after adding element)
    C2V_CREATE_VIEW_FROM_STATE: 'c2v:createViewFromState',  // Canvas requests Vue to create a new view from state and its connections
    
    // V2C: Vue → Canvas Messages
    V2C_SET_DOCUMENT: 'v2c:setDocument',
    V2C_SET_SHAPE_DATA: 'v2c:setShapeData',
    V2C_SET_THEME: 'v2c:setTheme',  // Vue sends theme change to canvas iframe
  };
  
  return {
    MessageTypes: MessageTypes,
    ShapeTypes: ShapeTypes,
  };
}));