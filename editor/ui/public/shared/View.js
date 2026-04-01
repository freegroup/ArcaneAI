

View = draw2d.Canvas.extend({
	
	init:function(id)
    {
		    this._super(id, 8000,8000);
        this.zoomingFactor = 1.2

        // 8-bit Retro style - phosphor green dots on dark background (like old CRT monitors)
        this.installEditPolicy(new draw2d.policy.canvas.ShowDotEditPolicy(20, 1, "#1f51a9", "#1a1a2e"));
        this.installEditPolicy(new EditPolicy())
        this.installEditPolicy(new draw2d.policy.connection.DragConnectionCreatePolicy({
            createConnection: () => {
                return new TriggerConnection();
            }
        }));
    
        // Mapping: ShapeType → CCM method name
        const shapeTypeToCCMMethod = {
            [ShapeTypes.STATE]: 'handleStateChange',
            [ShapeTypes.TRIGGER_LABEL]: 'handleStateTriggerChange',
            [ShapeTypes.TRIGGER_CONNECTION]: 'handleConnectionChange',
        };

        this.getCommandStack().addEventListener((e)=>{
            if(e.isPostChangeEvent()){
                // Get command details for granular change notification
                const command = e.getCommand();
                
                // Check if a new connection was added via CommandConnect
                // If so, select it and focus the name property field
                if (command instanceof draw2d.command.CommandConnect) {
                    const connection = command.getConnection();
                    if (connection) {
                        // Select the newly created connection after command execution completes
                        // Use setTimeout to ensure the connection is fully added to the canvas
                        setTimeout(() => {
                            this.setCurrentSelection(connection);
                            
                            // Send message to Vue to focus the triggerName property field
                            // Additional delay to ensure selection event is processed first
                            setTimeout(() => {
                                window.parent.postMessage({
                                    type: MessageTypes.C2V_FOCUS_PROPERTY,
                                    field: 'triggerName'
                                }, '*');
                            }, 50);
                        }, 0);
                    }
                }
                
                if (command?.getAffectedFigures) {
                    const affectedFigures = command.getAffectedFigures();
                    
                    // Send CCM message for each affected figure
                    affectedFigures.forEach(figure => {
                        const figureName = figure.NAME;
                        const ccmMethod = shapeTypeToCCMMethod[figureName];
                        
                        if (ccmMethod) {
                            window.parent.postMessage({
                                type: MessageTypes.C2V_CCM,
                                data: {
                                    method: ccmMethod,
                                    payload: figure.getPersistentAttributes()
                                }
                            }, '*');
                        }
                    });
                }
                
                var writer = new draw2d.io.json.Writer();
                writer.marshal(this, (json) => {
                  if( json.length ===0)
                    return
                      
                  window.parent.postMessage({ 
                      type: MessageTypes.C2V_DOCUMENT_UPDATED, 
                      data: json,
                      source: 'canvas:shared'
                  }, '*');
                
                });                
            }
        });

        let setZoom = (newZoom) => {
            let bb = this.getBoundingBox().getCenter()
            let c = $("#container")
            this.setZoom(newZoom)
            this.scrollTo((bb.y / newZoom - c.height() / 2), (bb.x / newZoom - c.width() / 2))
        }
      
        // ZoomIn Button and the callbacks
        $("#canvas_zoom_in").on("click", () => {
            setZoom(this.getZoom() * this.zoomingFactor)
        })
        Mousetrap.bindGlobal(['mod+-'], (event) => {
          setZoom(this.getZoom() * this.zoomingFactor)
          return false
        })


    
        // OneToOne Button
        $("#canvas_zoom_normal").on("click", () => {
            setZoom(1.0)
        })
    
        //ZoomOut Button and the callback
        $("#canvas_zoom_out").on("click", () => { 
            setZoom(this.getZoom() * (1/this.zoomingFactor))
        }) 
        // Mousetrap behandelt + und shift+= identisch, da + tatsächlich als Shift+= interpretiert wird.
        Mousetrap.bindGlobal(['mod+='], (event) => {
          setZoom(this.getZoom() * 1/this.zoomingFactor)
          return false
        })


        Mousetrap.bindGlobal(['h'], (event) => {
          if(this.getSelection().isEmpty()){
            return
          }
          this.getFigures()
            .each( (i,figure)=>{
              figure.setAlpha(0.1)
            })
            
          this.getLines().each( (i,line)=>{
            line.routingRequired = true
            line.setAlpha(0.1)
          })
          this.getSelection().each((i, f) => {
            f.setAlpha(1)
            f.getPorts().each((i, port) =>{
              port.getConnections().each( (i,con)=>{
                con.routingRequired = true
                con.setAlpha(1)
                con.getSourceParent().setAlpha(1.0)
                con.getTargetParent().setAlpha(1.0)
              })
            })
          })
          return false
        },"keydown")

        Mousetrap.bindGlobal(['h'], (event) => {
          this.getFigures().each( (i,line)=>{
            line.setAlpha(1)
          })
          this.getLines().each( (i,line)=>{
            line.setAlpha(1)
          })
          return false
        },"keyup")


        this.on("contextmenu", (emitter, event) => {
            let figure = this.getBestFigure(event.x, event.y)      
  
            if (figure !== null && figure instanceof Raft) {
              ContextMenu.show({
                x: event.x,
                y: event.y,
                canvas: this,
                items: {
                    "label": { name: "Add Label", callback: () => {
                        const userInput = prompt("Enter label text:");
                        if (userInput && userInput.trim()) {
                            let label = new draw2d.shape.basic.Label({
                              text: userInput.trim(),
                              stroke: 0, 
                              x: 20,
                              y: 40,
                              bold: true,
                              fontFamily: getVar('--global-font-family', 'Ithaca, monospace'), 
                            });
                            let locator = new draw2d.layout.locator.SmartDraggableLocator();
                            label.installEditor(new LabelInplaceEditor());
                            figure.add(label, locator);
                        }
                    }},
                    "delete": { name: "Delete", callback: () => {
                        this.getCommandStack().execute(new draw2d.command.CommandDelete(figure));
                    }}
                }
              });
            }
          })
	  },

    getFigure: function(id)
    {
        let result = null
        this.getFigures().each( (i, figure)=> {
            if(result !== null){
                return false
            }
            if(figure.id === id ){
                result = figure;
                return false
            }
            figure.children.each((i, entry) => {
                let child = entry.figure
                if(child.id === id ){
                    result = child;
                    return false
                }
              })
        });
        return result
    },


    setDocumentData: function(jsonData)
    {
        var reader = new draw2d.io.json.Reader();
        this.clear();
        reader.unmarshal(this, jsonData);
        this.centerDocument();
        return this;
    },

    /**
     * Silent inplace update of a shape's data.
     * This is called from PropertyEditor and should NOT trigger any events.
     * The model/view store is updated separately by the PropertyEditor.
     * 
     * IMPORTANT: This must remain silent to prevent circular updates that
     * would clear the canvas selection and hide the PropertyView.
     */
    setShapeData: function(data)
    {
        var shape = this.getFigure(data.id)
        if(shape){
            shape.attr(data)
        }
        else {
            shape = this.getLine(data.id)
            if(shape){
                shape.attr({
                    name: data.name,
                    userData: data.userData
                })
            }
        }
        // NO C2V_DOCUMENT_UPDATED - this is a silent update
        return this
    },

    deleteSelection: function()
    {
      var node = this.getPrimarySelection();
      if(node !== null){
        var command= new draw2d.command.CommandDelete(node);
        this.getCommandStack().execute(command);
      }
    },

    toggleFullScreen: function() 
    {
        var doc = window.document;
        var docEl = doc.documentElement;
      
        var requestFullScreen =
          docEl.requestFullscreen ||
          docEl.mozRequestFullScreen ||
          docEl.webkitRequestFullScreen ||
          docEl.msRequestFullscreen;
        
        var cancelFullScreen =
          doc.exitFullscreen ||
          doc.mozCancelFullScreen ||
          doc.webkitExitFullscreen ||
          doc.msExitFullscreen;
      
        if (
          !doc.fullscreenElement &&
          !doc.mozFullScreenElement &&
          !doc.webkitFullscreenElement &&
          !doc.msFullscreenElement
        ) {
          requestFullScreen.call(docEl);
        } else {
          cancelFullScreen.call(doc);
        }
    },
    
    getBoundingBox: function () 
    {
        let xCoords = []
        let yCoords = []
        this.getFigures().each( (i, f) => {
          let b = f.getBoundingBox()
          xCoords.push(b.x, b.x + b.w)
          yCoords.push(b.y, b.y + b.h)
        })
        this.getLines().each((i, f) => {
          let b = f.getBoundingBox()
          xCoords.push(b.x, b.x + b.w)
          yCoords.push(b.y, b.y + b.h)
        })
        let minX = Math.min.apply(Math, xCoords)
        let minY = Math.min.apply(Math, yCoords)
        let width = Math.max(100, Math.max.apply(Math, xCoords) - minX)
        let height = Math.max(100, Math.max.apply(Math, yCoords) - minY)
    
        return new draw2d.geo.Rectangle(minX, minY, width, height)
    },


    centerDocument: function () 
    {
        this.setZoom(1.0)
    
        let c = $("#container")
        if (this.getFigures().getSize() > 0) {
          // get the bounding box of the document and translate the complete document
          // into the center of the canvas. Scroll to the top left corner after them
          //
          let bb = this.getBoundingBox()
          this.scrollTo(bb.y - c.height() / 2 + bb.h / 2, bb.x - c.width() / 2 + bb.w / 2)
        } else {
          let bb = {
            x: this.getWidth() / 2,
            y: this.getHeight() / 2
          }
          this.scrollTo(bb.y - c.height() / 2, bb.x - c.width() / 2)
        }
    },

});

