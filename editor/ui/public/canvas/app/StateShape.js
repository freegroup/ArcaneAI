
let NORMAL_STYLE = {
    stroke: 1,
    fontColor: "#4f4f4f",  
    bgColor: "#add6f5", 
    color: "#349be8",
}

let START_STYLE = {
    stroke: 2,
    fontColor: "#6f6f6f",  
    bgColor: "#c3bae5", 
    color: "#654cb7",
}

let END_STYLE = {
    stroke: 2,
    fontColor: "#3f3f3f",
    bgColor: "#ffcccb",
    color: "#d9534f",
}

const StateType = Object.freeze({
    NORMAL: "NORMAL",
    START: "START",
    END: "END"
});

StateShape = draw2d.shape.layout.VerticalLayout.extend({

	NAME: "StateShape",
	
    init : function(attr, setter, getter)
    {
        this.start = false
        this.classLabel = new draw2d.shape.basic.Label({
            text:"TriggerName", 
            ...NORMAL_STYLE,
            radius: 10, 
            padding:10,
            bold:true,
            resizeable:true,
            editor:new draw2d.ui.LabelInplaceEditor()
        })
  
    	this._super(
            extend({
                bgColor:null, 
                color:"#d7d7d7", 
                stroke:0, 
                gap: 5,
                radius:3,
                stateType: StateType.NORMAL,
                userData: {
                    system_prompt: ""
                }
            },attr),
            extend({
              name: this.setName,
              stateType: this.setStateType,
            }, setter),
            extend({
              name: this.getName,
              stateType: this.getStateType,
            }, getter))
                 
        // flag which indicates if the figure should read/write ports to
        // JSON
        this.persistPorts = false
        this.createPort("input")
        this.createPort("output")

        this.add(this.classLabel);
        this.classLabel.on("contextmenu", (emitter, event)=>{
            $.contextMenu({
                selector: 'body', 
                events:{  
                    hide:()=> { $.contextMenu( 'destroy' ); }
                },
                callback: (key, options) =>{
                   switch(key){
                   case "delete":
                       this.getCanvas().getCommandStack().execute(
                            new draw2d.command.CommandDelete(this)
                        )
                       break;
                    case "add":
                        setTimeout(()=>{
                            this.addTrigger("_new_").onDoubleClick();
                        },10);
                        break;
                    case "start":
                        this.getCanvas().getCommandStack().execute(
                            new draw2d.command.CommandAttr(this, {stateType: StateType.START})
                        )
                        break;
                    case "normal":
                        this.getCanvas().getCommandStack().execute(
                            new draw2d.command.CommandAttr(this, {stateType: StateType.NORMAL})
                        )
                        break;
                    case "end":
                        this.getCanvas().getCommandStack().execute(
                            new draw2d.command.CommandAttr(this, {stateType: StateType.END})
                        )
                        break;
                    default:
                       break;
                   }
                },
                x:event.x,
                y:event.y,
                items: {
                    "add": {name: "Add Trigger"},
                    "sep1": "---------",
                    "start": {name: "Start Node"},
                    "normal": {name: "Normal Node"},
                    "end": {name: "End Node"},
                    "sep2": "---------",
                    "delete": {name: "Delete"},
                }
            })
        })
    },
     
    setStateType: function(stateType) 
    {
        if (stateType === this.stateType) return this;

        // Deselect any other START nodes if setting a new START node
        if (stateType === StateType.START && this.canvas !== null) {
            this.canvas.getFigures().each((i, f) => {
                if (f !== this && f.getStateType?.() === StateType.START) {
                    f.setStateType?.(StateType.NORMAL);
                }
            });
        }

        this.stateType = stateType;

        if (this.stateType === StateType.START) {
            this.classLabel.attr(START_STYLE);
        } else if (this.stateType === StateType.END) {
            this.classLabel.attr(END_STYLE);
        } else {
            this.classLabel.attr(NORMAL_STYLE);
        }

        return this;
    },

    
    getStateType: function()
    {
        return this.stateType
    },

    
    setAlpha: function(alpha)
    {
        this._super(alpha)
        this.classLabel.setAlpha(alpha)
        this.children.each(function(i,e){
            e.figure.setAlpha(alpha)
        })
        this.getPorts().each(function(i,p){
            p.setAlpha(alpha)
        })
        
    },

    /**
     * @method
     * Add an entity to the db shape
     * 
     * @param {String} txt the label to show
     * @param {Number} [optionalIndex] index where to insert the entity
     */
    addTrigger: function(txt, optionalIndex)
    {
	   	 var label =new TriggerLabel(txt);
         
         var _table=this;
         label.on("contextmenu", (emitter, event)=>{
             $.contextMenu({
                 selector: 'body', 
                 events:
                 {  
                     hide:()=>{ $.contextMenu( 'destroy' ); }
                 },
                 callback: (key, options) =>
                 {
                    switch(key){
                    case "rename":
                        setTimeout(()=>{
                            emitter.onDoubleClick();
                        },10);
                        break;
                    case "new":
                        setTimeout(()=>{
                            _table.addTrigger("_new_").onDoubleClick();
                        },10);
                        break;
                    case "delete":
                        // with undo/redo support
                        var cmd = new draw2d.command.CommandDelete(emitter);
                        emitter.getCanvas().getCommandStack().execute(cmd);
                    default:
                        break;
                    }
                 },
                 x:event.x,
                 y:event.y,
                 items: 
                 {
                    "new": {name: "Add Trigger"},
                    "rename": {name: "Rename Trigger"},
                    "sep1":   "---------",
                     "delete": {name: "Delete Trigger"}
                 }
             });
         });
         
	     if($.isNumeric(optionalIndex)){
             this.add(label, null, optionalIndex+1);
	     }
	     else{
	         this.add(label);
	     }
         label.setSelectionAdapter(null);

	     return label;
    },
    
    /**
     * @method
     * Remove the entity with the given index from the DB table shape.<br>
     * This method removes the entity without care of existing connections. Use
     * a draw2d.command.CommandDelete command if you want to delete the connections to this entity too
     * 
     * @param {Number} index the index of the entity to remove
     */
    removeTrigger: function(index)
    {
        this.remove(this.children.get(index+1).figure);
    },

    /**
     * @method
     * Returns the entity figure with the given index
     * 
     * @param {Number} index the index of the entity to return
     */
    getTrigger: function(index)
    {
        return this.children.get(index+1).figure;
    },
     

     /**
      * @method
      * Set the name of the DB table. Visually it is the header of the shape
      * 
      * @param name
      */
    setName: function(name)
    {
        this.classLabel.setText(name);
        return this;
    },
     
     
    getName: function()
    {
        return this.classLabel.getText();
    },
     
     /**
      * @method 
      * Return an objects with all important attributes for XML or JSON serialization
      * 
      * @returns {Object}
      */
     getPersistentAttributes : function()
     {
        var memento= this._super();

        memento.name = this.classLabel.getText();
        memento.stateType = this.stateType ?? StateType.NORMAL
        memento.trigger   = [];

        this.children.each(function(i,e){
            if(i>0){ // skip the header of the figure
                memento.trigger.push({
                    id: e.figure.getId(),
                    name:e.figure.getName(),
                    description:e.figure.getDescription(),
                    sound_effect:e.figure.getSoundEffect(),
                    sound_effect_duration:e.figure.getSoundEffectDuration(),
                    sound_effect_volume:e.figure.getSoundEffectVolume(),
                    system_prompt: e.figure.getSystemPrompt(),
                    conditions: e.figure.getConditions(),
                    actions: e.figure.getActions()
                });
            }
        });

        delete memento.alpha
        delete memento.stroke
     
         return memento;
     },
     
     /**
      * @method 
      * Read all attributes from the serialized properties and transfer them into the shape.
      *
      * @param {Object} memento
      * @return
      */
     setPersistentAttributes : function(memento)
     {
        delete memento.alpha
        delete memento.stroke

        this._super(memento);
         
        this.setName(memento.name);
        this.setStateType(memento.stateType ?? StateType.NORMAL)

         if(typeof memento.trigger !== "undefined"){
             $.each(memento.trigger, $.proxy(function(i,e){
                 var trigger =this.addTrigger(e.name ?? "undefined");
                 trigger.setConditions(e.conditions ?? [])
                 trigger.setActions(e.actions ?? [])
                 trigger.setDescription(e.description ?? "")
                 trigger.setSoundEffect(e.sound_effect ?? "")
                 trigger.setSoundEffectDuration(e.sound_effect_duration ?? 2)
                 trigger.setSoundEffectVolume(e.sound_effect_volume ?? 100)
                 trigger.setSystemPrompt(e.system_prompt ?? "")
             },this));
         }

         return this;
     }  

});
