/**
 * Icon for "fire only once" actions: a ring with a "1" inside.
 * Same 32×32 path format as the draw2d icons (e.g. draw2d.shape.icon.Lock).
 */
var OnceIcon = draw2d.shape.icon.Icon.extend({
    NAME: "OnceIcon",

    init: function(attr, setter, getter)
    {
        this._super({width: 50, height: 50, ...attr}, setter, getter);
    },

    createSet: function()
    {
        return this.canvas.paper.path(
            // ring: outer circle, inner circle drawn the other way round (hole)
            "M3,16a13,13 0 1,0 26,0a13,13 0 1,0 -26,0z" +
            "M5.5,16a10.5,10.5 0 1,1 21,0a10.5,10.5 0 1,1 -21,0z" +
            // the "1"
            "M17.5,9L17.5,21L20,21L20,23L12,23L12,21L14.5,21L14.5,12.6L11.8,14.2L11.8,11.8L15.2,9z"
        );
    }
});
