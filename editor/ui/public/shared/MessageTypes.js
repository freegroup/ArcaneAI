/**
 * Message Types Contract for Canvas ↔ Vue Communication
 * 
 * This file uses UMD (Universal Module Definition) pattern to work in both:
 * - Browser global scope (for draw2d canvas code)
 * - ES6 modules (for Vue components)
 * 
 * Usage in Browser (canvas):
 *   <script src="./MessageTypes.js"></script>
 *   window.parent.postMessage({ type: MessageTypes.CANVAS_READY }, origin);
 * 
 * Usage in Vue:
 *   import MessageTypes from '../../public/canvas/MessageTypes.js';
 *   if (message.type === MessageTypes.CANVAS_READY) { ... }
 */

/* eslint-disable no-undef */
(function (root, factory) {
  if (typeof define === 'function' && define.amd) {
    // AMD
    define([], factory);
  } else if (typeof module === 'object' && module.exports) {
    // Node/CommonJS
    module.exports = factory();
  } else if (typeof exports === 'object') {
    // ES6 Module
    exports.MessageTypes = factory();
  } else {
    // Browser global
    root.MessageTypes = factory();
  }
}(typeof self !== 'undefined' ? self : this, function () {
  
  const MessageTypes = {
    // ====================================
    // Canvas → Vue Messages
    // ====================================
    
    /**
     * Sent by canvas when it's fully loaded and ready to receive messages
     * Payload: none
     */
    CANVAS_READY: 'canvasReady',
    
    /**
     * Sent by canvas when the document (diagram) has been modified
     * Payload: { data: Array<Shape> } - Full diagram array
     */
    DOCUMENT_UPDATED: 'updateDocumentData',
    
    /**
     * Sent by canvas when a shape is selected
     * Payload: { event: 'onSelect', type: ShapeType, data: ShapeData }
     */
    SELECT: 'onSelect',
    
    /**
     * Sent by canvas when selection is cleared
     * Payload: { event: 'onUnselect' }
     */
    UNSELECT: 'onUnselect',
    
    /**
     * Sent by canvas to toggle fullscreen mode
     * Payload: none
     */
    TOGGLE_FULLSCREEN: 'toggleFullScreen',
    
    // ====================================
    // Vue → Canvas Messages
    // ====================================
    
    /**
     * Sent by Vue to set the entire document/diagram
     * Payload: { type: 'setDocument', data: Array<Shape> }
     */
    SET_DOCUMENT: 'setDocument',
    
    /**
     * Sent by Vue to update a single shape's data
     * Payload: { type: 'setShapeData', data: ShapeData }
     */
    SET_SHAPE_DATA: 'setShapeData',
    
    // ====================================
    // Shape Types
    // ====================================
    
    /**
     * State shape type identifier
     */
    SHAPE_STATE: 'StateShape',
    
    /**
     * Trigger label shape type identifier
     */
    SHAPE_TRIGGER_LABEL: 'TriggerLabel',
    
    /**
     * Trigger connection shape type identifier
     */
    SHAPE_TRIGGER_CONNECTION: 'TriggerConnection',
  };
  
  // Helper functions for creating messages
  MessageTypes.createMessage = function(type, data, source) {
    const message = { type: type, data: data };
    if (source) {
      message.source = source;
    }
    return message;
  };
  
  MessageTypes.createSelectMessage = function(shapeType, data, source) {
    const message = { 
      event: MessageTypes.SELECT, 
      type: shapeType, 
      data: data 
    };
    if (source) {
      message.source = source;
    }
    return message;
  };
  
  MessageTypes.createUnselectMessage = function(source) {
    const message = { event: MessageTypes.UNSELECT };
    if (source) {
      message.source = source;
    }
    return message;
  };
  
  return MessageTypes;
}));