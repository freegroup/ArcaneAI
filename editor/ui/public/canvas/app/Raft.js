Raft = draw2d.shape.composite.Raft.extend({

    NAME : "Raft",

    init : function(attr, setter, getter)
    {
        this._super(extend({
            bgColor:"#555555", 
            color:"#000000"
        },attr), setter, getter);
    },

    getParameterSettings: function()
    {
        return [];
    },

     
    setStateType: function(flag)
    {
        return this
    },
    
    /**
     * @method
     * Return an objects with all important attributes for XML or JSON serialization
     *
     * @returns {Object}
     */
    getPersistentAttributes : function()
    {
        var memento = this._super();

        // add all decorations to the memento
        //
        memento.labels = [];
        this.children.each(function(i,e){
            var labelJSON = e.figure.getPersistentAttributes();
            labelJSON.locator=e.locator.NAME;
            memento.labels.push(labelJSON);
        });

        delete memento.cssClass;
        delete memento.alpha
        delete memento.bgColor
        delete memento.color

        return memento;
    },

    /**
     * @method
     * Read all attributes from the serialized properties and transfer them into the shape.
     *
     * @param {Object} memento
     * @returns
     */
    setPersistentAttributes : function(memento)
    {
        delete memento.alpha
        delete memento.bgColor
        delete memento.color

        this._super(memento);
        
        // remove all decorations created in the constructor of this element
        //
        this.resetChildren();

        // and add all children of the JSON document.
        //
        $.each(memento.labels, $.proxy(function(i,json){
            // create the figure stored in the JSON
            var figure =  eval("new "+json.type+"()");

            // apply all attributes
            figure.attr(json);

            // instantiate the locator
            var locator =  eval("new "+json.locator+"()");

            // add the new figure as child to this figure
            this.add(figure, locator);
        },this));
    }
});
