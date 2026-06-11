var TriggerLabel = draw2d.shape.box.HBox.extend({
    NAME: "TriggerLabel",

    init: function(txt)
    {
        const fontSize   = parseInt(getVar('--global-font-size', '20'));
        const fontFamily = getVar('--global-font-family', 'Ithaca, monospace');
        const fontColor  = getVar('--connection-label-font', '#3f3f34');

        this._super({
            stroke:     parseInt(getVar('--label-stroke', '2')),
            radius:     5,
            padding:    {left: 10, top: 5, right: 10, bottom: 5},
            bgColor:    getVar('--connection-label-bg', '#cce5bc'),
            color:      getVar('--color-accent-2', '#f39c12'),
            resizeable: true,
            gap:        0,
            cssClass:   "cursor-pointer",
            userData: {
                actions:     [],
                conditions:  [],
                system_prompt: "",
            }
        });

        // Lock icon — shown only when conditions exist
        this.lockIcon = new draw2d.shape.icon.Lock({
            width:      20,
            height:     20,
            color:      fontColor,
            bgColor:    "none",
            resizeable: false,
            visible:    false,
        });

        // Text label — carries the inline editor
        this.textLabel = new draw2d.shape.basic.Label({
            text:       txt,
            stroke:     0,
            bgColor:    "none",
            color:      "none",
            fontColor:  fontColor,
            fontSize:   fontSize,
            fontFamily: fontFamily,
            editor:     new draw2d.ui.LabelEditor(),
            selectable: false,
            draggable:  false,
        });

        this.add(this.lockIcon);
        this.add(this.textLabel);

        this.installEditPolicy(new draw2d.policy.figure.AntSelectionFeedbackPolicy({
            color:    getVar('--selection-color', '#e94560'),
            stroke:   parseInt(getVar('--selection-stroke', '6')),
            dasharray: "- "
        }));

        this.on("change:userData", (emitter, event) => {
            this.updateStyle();
        });
    },

    // Delegate double-click to the inner text label so the inline editor fires
    onDoubleClick: function()
    {
        this.textLabel.onDoubleClick();
    },

    updateStyle: function()
    {
        const hasConditions = this.getUserData()?.conditions?.length > 0;
        this.attr("dasharray", hasConditions ? "- " : null);
        this.lockIcon.setVisible(hasConditions);
    },

    // ── Getters / Setters ─────────────────────────────────────────────────────

    setName: function(name)
    {
        this.textLabel.setText(name);
        return this;
    },

    getName: function()
    {
        return this.textLabel.getText();
    },

    getSystemPrompt: function()   { return this.getUserData().system_prompt; },
    setSystemPrompt: function(v)  { this.getUserData().system_prompt = v; },

    getDescription: function()    { return this.getUserData().description; },
    setDescription: function(v)   { this.getUserData().description = v; },

    getSoundEffect: function()         { return this.getUserData().sound_effect; },
    setSoundEffect: function(v)        { this.getUserData().sound_effect = v; },

    getSoundEffectDuration: function() { return this.getUserData().sound_effect_duration; },
    setSoundEffectDuration: function(v){ this.getUserData().sound_effect_duration = v; },

    getSoundEffectVolume: function()   { return this.getUserData().sound_effect_volume; },
    setSoundEffectVolume: function(v)  { this.getUserData().sound_effect_volume = v; },

    getConditions: function()
    {
        return this.getUserData().conditions;
    },

    setConditions: function(conditions)
    {
        this.getUserData().conditions = conditions;
        this.updateStyle();
    },

    getActions: function()    { return this.getUserData().actions; },
    setActions: function(v)   { this.getUserData().actions = v; },

    onDrag: function(dx, dy, dx2, dy2, shiftKey, ctrlKey)
    {
        return false;
    },
});
