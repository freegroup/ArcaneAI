/**
 * A custom SelectionFeedbackPolicy for connections.
 * Extends LineSelectionFeedbackPolicy to add visual feedback (color, stroke, outline)
 * while keeping the standard resize handles functionality.
 * 
 * @extends draw2d.policy.line.LineSelectionFeedbackPolicy
 */
var TriggerSelectionFeedbackPolicy = draw2d.policy.line.LineSelectionFeedbackPolicy.extend({
  
  NAME: "TriggerSelectionFeedbackPolicy",

  /**
   * Constructor
   */
  init: function(attr, setter, getter) {
    this._super(attr, setter, getter);
  },

  /**
   * Called when the figure is selected.
   * Store original attributes and apply selection feedback.
   * 
   * @param {draw2d.Canvas} canvas - The canvas
   * @param {draw2d.Figure} figure - The figure being selected (should be a Connection)
   * @param {Boolean} isPrimarySelection - Whether this is the primary selection
   */
  onSelect: function(canvas, figure, isPrimarySelection) {
    this._super(canvas, figure, isPrimarySelection);
    
    if (figure.setHighlight) {
        figure.setHighlight();
    }
  },

  /**
   * Called when the figure is unselected.
   * Restore original attributes.
   * 
   * @param {draw2d.Canvas} canvas - The canvas
   * @param {draw2d.Figure} figure - The figure being unselected
   */
  onUnselect: function(canvas, figure) {
    this._super(canvas, figure);
    if (figure.resetHighlight) {
        figure.resetHighlight();
    }
  },

});
