/**
 * Custom Router that extends InteractiveManhattanBridgedConnectionRouter but installs our own SelectionFeedbackPolicy.
 * This allows connections to use our custom TriggerSelectionFeedbackPolicy for visual feedback.
 * 
 * @extends draw2d.layout.connection.InteractiveManhattanBridgedConnectionRouter
 */
var TriggerRouter = draw2d.layout.connection.InteractiveManhattanBridgedConnectionRouter.extend({
  
  NAME: "TriggerRouter",

  /**
   * Override onInstall to install our custom TriggerSelectionFeedbackPolicy
   * instead of the default LineSelectionFeedbackPolicy.
   * 
   * @param {draw2d.Connection} connection - The connection this router is installed on
   */
  onInstall: function(connection) {
    this._super(connection);

    // Install our custom SelectionFeedbackPolicy
    connection.installEditPolicy(new TriggerSelectionFeedbackPolicy());
  }
});
