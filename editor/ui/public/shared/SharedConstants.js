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
  const MessageTypes = {
    // Canvas → Vue Messages
    CANVAS_READY: 'canvasReady',
    DOCUMENT_UPDATED: 'updateDocumentData',
    ELEMENT_UPDATED: 'updateElementData',
    SELECT: 'onSelect',
    UNSELECT: 'onUnselect',
    CCM: 'ccm',  // Canvas notifies Vue about content changes (for ContentChangeManager)
    
    // Vue → Canvas Messages
    SET_DOCUMENT: 'documentUpdated',
    SET_SHAPE_DATA: 'figureUpdated',
  };
  
  return {
    MessageTypes: MessageTypes,
    ShapeTypes: ShapeTypes,
  };
}));