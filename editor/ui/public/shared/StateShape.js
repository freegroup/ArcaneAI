function getStateStyles() {
    let _font = getVar('--global-font-family', 'Ithaca, monospace');
    let _fontSize = parseInt(getVar('--global-font-size', '24'));
    let _stroke = parseInt(getVar('--state-stroke', '4'));
    return {
        NORMAL: {
            stroke: _stroke,
            fontSize: _fontSize,
            fontFamily: _font,
            radius: parseInt(getVar('--state-normal-radius', '1')),
            fontColor: getVar('--state-normal-font', '#f39c12'),
            bgColor: getVar('--state-normal-bg', '#0f3460'),
            color: getVar('--state-normal-border', '#349be8'),
        },
        START: {
            stroke: _stroke,
            fontSize: _fontSize,
            fontFamily: _font,
            radius: parseInt(getVar('--state-start-radius', '1')),
            padding:20,
            fontColor: getVar('--state-start-font', '#03c524'),
            bgColor: getVar('--state-start-bg', '#281b58'),
            color: getVar('--state-start-border', '#c6bee1'),
        },
        END: {
            stroke: _stroke,
            fontSize: _fontSize,
            fontFamily: _font,
            radius: parseInt(getVar('--state-end-radius', '1')),
            fontColor: getVar('--state-end-font', '#3f3f3f'),
            bgColor: getVar('--state-end-bg', '#ffcccb'),
            color: getVar('--state-end-border', '#d9534f'),
        }
    };
}

const StateType = Object.freeze({
    NORMAL: "NORMAL",
    START: "START",
    END: "END"
});

StateShape = draw2d.shape.box.VBox.extend({

	NAME: "StateShape",
	
    init : function(attr, setter, getter)
    {
        var styles = getStateStyles();
        this.start = false
        this.stateNameLabel = new draw2d.shape.basic.Label({
            text:"StateName",
            ...styles.NORMAL,
            radius: parseInt(getVar('--state-label-radius', '5')),
            padding:4,
            bold:false,
            resizeable:true,
            cssClass: "cursor-move",
            textAlign: "center"
        })
  
    	this._super(
            {
                bgColor:"#0000001F", 
                color:"#d7d7d7", 
                stroke:0, 
                gap: 5,
                radius:10,
                padding: 8,
                stateType: StateType.NORMAL,
                userData: {
                    system_prompt: ""
                }
            ,...attr},
            {
              name: this.setName,
              stateType: this.setStateType
            , ...setter},
            {
              name: this.getName,
              stateType: this.getStateType
            , ...getter})
                 
        // flag which indicates if the figure should read/write ports to
        // JSON
        this.persistPorts = false
        this.createPort("input")
        this.createPort("output")

        this.installEditPolicy(new draw2d.policy.figure.AntSelectionFeedbackPolicy({
           color: getVar('--selection-color', '#e94560'),
           stroke: parseInt(getVar('--selection-stroke', '6')),
           dasharray: "- "
        }));
  
        this.add(this.stateNameLabel);
        this.stateNameLabel.on("contextmenu", (emitter, event) => {
            ContextMenu.show({
                x: event.x,
                y: event.y,
                canvas: this.getCanvas(),
                items: {
                    "add": { name: "Add Trigger", callback: () => {
                        setTimeout(() => this.addTrigger("_new_").onDoubleClick(), 10);
                    }},
                    "sep1": {},
                    "chatFromHere": { name: "Chat from here", icon: "fa-comments", callback: () => {
                        window.parent.postMessage({
                            type: MessageTypes.C2V_CHAT_FROM_HERE,
                            stateName: this.getName()
                        }, '*');
                    }},
                    "viewFromHere": { name: "View from Here...", icon: "fa-eye", callback: () => {
                        this.createViewFromHere();
                    }},
                    "sep2": {},
                    "start": { name: "Set as Start", callback: () => {
                        this.setStateType(StateType.START);
                        window.parent.postMessage({ type: MessageTypes.C2V_MODEL_CHANGED }, '*');
                    }},
                    "delete": { name: "Delete", callback: () => {
                        this.getCanvas().getCommandStack().execute(new draw2d.command.CommandDelete(this));
                    }}
                }
            });
        });
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
        var styles = getStateStyles();

        if (this.stateType === StateType.START) {
            this.stateNameLabel.attr(styles.START);
        } else if (this.stateType === StateType.END) {
            this.stateNameLabel.attr(styles.END);
        } else {
            this.stateNameLabel.attr(styles.NORMAL);
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
        this.stateNameLabel.setAlpha(alpha)
        this.children.each((i,e) => {
            e.figure.setAlpha(alpha)
        })
        this.getPorts().each((i,p) => {
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
         label.on("contextmenu", (emitter, event) => {
             ContextMenu.show({
                 x: event.x,
                 y: event.y,
                 canvas: _table.getCanvas(),
                 items: {
                    "new": { name: "Add Trigger", callback: () => {
                        setTimeout(() => _table.addTrigger("_new_").onDoubleClick(), 10);
                    }},
                    "rename": { name: "Rename Trigger", callback: () => {
                        setTimeout(() => emitter.onDoubleClick(), 10);
                    }},
                    "sep1": {},
                    "delete": { name: "Delete Trigger", callback: () => {
                        var cmd = new draw2d.command.CommandDelete(emitter);
                        emitter.getCanvas().getCommandStack().execute(cmd);
                    }}
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
        this.stateNameLabel.setText(name);
        return this;
    },
     
     
    getName: function()
    {
        return this.stateNameLabel.getText();
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

        memento.name = this.stateNameLabel.getText();
        memento.stateType = this.stateType ?? StateType.NORMAL
        memento.trigger   = [];

        this.children.each((i,e) => {
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
        memento.x = memento.x |0
        memento.y = memento.y |0
        
        delete memento.alpha
        delete memento.stroke
        delete memento.selectable
        delete memento.draggable
        delete memento.angle
        delete memento.cssClass
        delete memento.bgColor
        delete memento.color
        delete memento.radius
        delete memento.dasharray
        delete memento.gap
        delete memento.align
        delete memento.width
        delete memento.height
        delete memento.fontFamily

         return memento;
     },
     
    /**
     * @method
     * Creates a new view from this state and all directly connected states/connections.
     * Sends the view data to Vue which will show a dialog for naming.
     */
    createViewFromHere: function()
    {
        const canvas = this.getCanvas();
        if (!canvas) return;
        
        // Collect all connected states and connections (same logic as 'h' key highlight)
        const collectedStates = new Set();
        const collectedConnections = new Set();
        
        // Add this state
        collectedStates.add(this);
        
        // Get all connections from this state's ports
        this.getPorts().each((i, port) => {
            port.getConnections().each((i, con) => {
                collectedConnections.add(con);
                // Add connected states
                const sourceParent = con.getSourceParent();
                const targetParent = con.getTargetParent();
                if (sourceParent && sourceParent.NAME === "StateShape") {
                    collectedStates.add(sourceParent);
                }
                if (targetParent && targetParent.NAME === "StateShape") {
                    collectedStates.add(targetParent);
                }
            });
        });
        
        // Serialize states with original positions
        const states = [];
        collectedStates.forEach(state => {
            const memento = state.getPersistentAttributes();
            states.push(memento);
        });
        
        // Serialize connections with routing info
        const connections = [];
        collectedConnections.forEach(con => {
            const memento = con.getPersistentAttributes();
            connections.push(memento);
        });
        
        // Build view data
        const viewData = [...states, ...connections];
        
        // Send request to Vue to show the dialog
        // Vue will use EncounterNewDialog with pre-filled name
        window.parent.postMessage({
            type: MessageTypes.C2V_CREATE_VIEW_FROM_STATE,
            defaultName: this.getName(),
            viewData: viewData
        }, '*');
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
        delete memento.bgColor
        delete memento.radius
        delete memento.width
        delete memento.height
        delete memento.fontFamily

        this._super(memento);
         
        this.setName(memento.name);
        this.setStateType(memento.stateType ?? StateType.NORMAL)
        this.stateNameLabel.setCssClass("cursor-move");

         if(typeof memento.trigger !== "undefined"){
             $.each(memento.trigger, (i,e) => {
                 var trigger =this.addTrigger(e.name ?? "undefined");
                 trigger.setConditions(e.conditions ?? [])
                 trigger.setActions(e.actions ?? [])
                 trigger.setDescription(e.description ?? "")
                 trigger.setSoundEffect(e.sound_effect ?? "")
                 trigger.setSoundEffectDuration(e.sound_effect_duration ?? 2)
                 trigger.setSoundEffectVolume(e.sound_effect_volume ?? 100)
                 trigger.setSystemPrompt(e.system_prompt ?? "")
             });
         }

         return this;
     }  

});
