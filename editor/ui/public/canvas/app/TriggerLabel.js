var TriggerLabel = draw2d.shape.basic.Label.extend({
    NAME: "TriggerLabel",

    init:function(txt)
    {
        this._super({
            text:txt,
            padding:{left:10, top:5, right:10, bottom:5},
            resizeable:true,
            radius: 10,
            fontColor:"#3f3f34",
            fontSize: 8,
            bgColor: "#cce5bc",
            color : "#7fc256",
            editor:new draw2d.ui.LabelEditor(),
            userData: {
                actions: [],
                conditions: [],
                system_prompt: "",
              }
        },
        {
            name: this.setName,
            description: this.setDescription,
            system_prompt: this.setSystemPrompt,
        },
        {
            name: this.getName,
            description: this.getDescription,
            system_prompt: this.getSystemPrompt,
        });

        this.on("change:userData", (emitter, event)=>{
            this.updateStyle()
        })
    },

    updateStyle: function()
    {
        this.attr("dasharray", this.attr("userData")?.conditions?.length >0?"- ":null)
    },

    getSystemPrompt: function()
    {
        return this.getUserData().system_prompt
    },

    setSystemPrompt: function(system_prompt)
    {
        this.getUserData().system_prompt = system_prompt
    },


    getDescription: function()
    {
        return this.getUserData().description
    },

    setDescription: function(description)
    {
        this.getUserData().description = description
    },


    getSoundEffect: function()
    {
        return this.getUserData().sound_effect
    },

    setSoundEffect: function(sound_effect)
    {
        this.getUserData().sound_effect = sound_effect
    },


    getSoundEffectDuration: function()
    {
        return this.getUserData().sound_effect_duration
    },

    setSoundEffectDuration: function(sound_effect_duration)
    {
        this.getUserData().sound_effect_duration = sound_effect_duration
    },


    getSoundEffectVolume: function()
    {
        return this.getUserData().sound_effect_volume
    },

    setSoundEffectVolume: function(sound_effect_volume)
    {
        this.getUserData().sound_effect_volume = sound_effect_volume
    },

    
    getConditions: function()
    {
        return this.getUserData().conditions
    },

    setConditions: function(conditions)
    {
        this.getUserData().conditions = conditions
        this.updateStyle()
    },

    getActions: function()
    {
        return this.getUserData().actions
    },

    setActions: function(actions)
    {
        this.getUserData().actions = actions
    },

    /**
     * @method
     * Set the name of the DB table. Visually it is the header of the shape
     * 
     * @param name
     */
    setName: function(name)
    {
        this.setText(name)
        return this
    },
      
    getName: function()
    {
        return this.getText()
    },
      
    onDrag: function(dx, dy, dx2, dy2, shiftKey, ctrlKey)
    {
        return false
    },
});
