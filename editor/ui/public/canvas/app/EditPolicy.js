EditPolicy = draw2d.policy.canvas.BoundingboxSelectionPolicy.extend({

    init: function () 
    {
      this._super()
    },

    onMouseUp: function (canvas, x, y, shiftKey, ctrlKey) 
    {
      if (shiftKey === true && this.mouseDownElement === null) {
        let rx = Math.min(x, this.x)
        let ry = Math.min(y, this.y)
        let rh = Math.abs(y - this.y)
        let rw = Math.abs(x - this.x)
        let raftFigure = new Raft()
        raftFigure.attr({
          x: rx,
          y: ry,
          width: rw,
          height: rh,
          opacity: 0.7,
          stroke: 1,
          color: "#d3e2fe",
          bgColor: "#f3f6fc"
        })
        canvas.add(raftFigure)
        this.boundingBoxFigure1.setCanvas(null)
        this.boundingBoxFigure1 = null
        this.boundingBoxFigure2.setCanvas(null)
        this.boundingBoxFigure2 = null
      }
      else {
        this._super(canvas, x, y, shiftKey, ctrlKey)
      }
    },

  })
  