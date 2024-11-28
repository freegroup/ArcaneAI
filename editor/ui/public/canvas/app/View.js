

View = draw2d.Canvas.extend({
	
	init:function(id)
    {
		    this._super(id, 8000,8000);
        this.zoomingFactor = 1.2

        this.installEditPolicy(new draw2d.policy.canvas.ShowGridEditPolicy({bgColor: "#333", color:"#222"}));
        this.installEditPolicy(new EditPolicy())
        this.installEditPolicy(new draw2d.policy.connection.DragConnectionCreatePolicy({
            createConnection: function(){
                return new TriggerConnection();
            }
        }));
    
        this.getCommandStack().addEventListener((e)=>{
            if(e.isPostChangeEvent()){
                var writer = new draw2d.io.json.Writer();
                writer.marshal(this, function(json){
                    if( json.length ===0)
                        return
                    window.parent.postMessage({ type: 'updateDocumentData', data: json }, '*');
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
            line.setAlpha(0.1)
          })
          this.getSelection().each((i, f) => {
            f.setAlpha(1)
            f.getPorts().each((i, port) =>{
              port.getConnections().each( (i,con)=>{
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
  
            if (figure !== null) {
              let {x,y} = event
              let items = null
      
              if (figure instanceof Raft) {
                items = {
                    "label":  {name: "Add Label"},
                    "delete": {name: "Delete"},
                }
              } 

              if(items){
                $.contextMenu({
                  selector: 'body',
                  events: {
                    hide: () => {
                      $.contextMenu('destroy')
                    }
                  },
                  callback: (key, options) => {
                    switch (key) {
                      case "label":
                        $("#inputModal").modal("show");

                        // Handle the modal's save button
                        const saveButton = document.getElementById("modalSaveButton");
                        const inputField = document.getElementById("modalInput");
          
                        // Clear previous input
                        inputField.value = "";
          
                        const saveHandler = () => {
                          const userInput = inputField.value.trim();
                          if (userInput) {
                            let label = new draw2d.shape.basic.Label({text: userInput,stroke: 0, x: -20,y: -40,bold: true,});
                            let locator = new draw2d.layout.locator.SmartDraggableLocator();
                            label.installEditor(new LabelInplaceEditor());
                            figure.add(label, locator);
                          }
                          // Cleanup modal
                          $("#inputModal").modal("hide");
                          saveButton.removeEventListener("click", saveHandler); // Remove event listener to avoid duplicates
                        };
          
                        saveButton.addEventListener("click", saveHandler);
                        break
                      case "delete":
                        this.getCommandStack().execute(new draw2d.command.CommandDelete(figure))
                        break
                    }
                  },
                  x: x,
                  y: y,
                  items: items
                })
              }
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
            figure.children.each(function (i, entry) {
                let child = entry.figure
                if(child.id === id ){
                    result = child;
                    return false
                }
              })
        });
        return result
    },


    setShapeData: function(data)
    {
        var shape = this.getFigure(data.id)
        if(shape){
            shape.attr(data)
        }
        else {
            shape = this.getLine(data.id)
            if(shape){
                shape.attr( {
                    name: data.name,
                    userData: data.userData
                })
            }
        }
        var writer = new draw2d.io.json.Writer();
        writer.marshal(this, function(json){
            if( json.length ===0)
                return
            window.parent.postMessage({ type: 'updateDocumentData', data: json }, '*');
        });                

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
        //window.parent.postMessage({ type: 'toggleFullScreen' }, '*');
        
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

