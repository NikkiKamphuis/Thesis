
var CustomGridVisualization = function(width, height, gridWidth, gridHeight, context, interactionHandler) {

    // Find cell size:
//     var cellWidth = Math.floor(width / gridWidth);
//     var cellHeight = Math.floor(height / gridHeight);
    var cellWidth = width / gridWidth;
    var cellHeight = height / gridHeight;

    // Find max radius of the circle that can be inscribed (fit) into the
    // cell of the grid.
    var maxR = Math.min(cellHeight, cellWidth)/2 - 1;

    

    // Calls the appropriate shape(agent)
    this.drawLayer = function(portrayalLayer, images) {
            
            // Re-initialize the lookup table
            (interactionHandler) ? interactionHandler.mouseoverLookupTable.init() : null
            
            // this.drawBackground(images[4],width, height)

            for (var i in portrayalLayer) {
                    var p = portrayalLayer[i];
                    // console.log(p)

                    // If p.Color is a string scalar, cast it to an array.
                    // This is done to maintain backwards compatibility
                    if (!Array.isArray(p.Color))
                            p.Color = [p.Color];

                    // Does the inversion of y positioning because of html5
                    // canvas y direction is from top to bottom. But we
                    // normally keep y-axis in plots from bottom to top.
                    p.y = gridHeight - p.y - 1;

                    // if a handler exists, add coordinates for the portrayalLayer index
                    (interactionHandler) ? interactionHandler.mouseoverLookupTable.set(p.x, p.y, i) : null;
                    // If the stroke color is not defined, then the first color in the colors array is the stroke color.
                    if (!p.stroke_color)
                            p.stroke_color = p.Color[0]

                    if (p.Shape == "rect")
                            this.drawRectangle(p.x, p.y, p.w, p.h, p.Color, p.stroke_color, p.Filled, p.text, p.text_color);
                    else if (p.Shape == "circle")
                            this.drawCircle(p.x, p.y, p.r, p.Color, p.stroke_color, p.Filled, p.text, p.text_color);
                    else if (p.Shape == "arrowHead")
                            this.drawArrowHead(p.x, p.y, p.heading_x, p.heading_y, p.scale, p.Color, p.stroke_color, p.Filled, p.text, p.text_color);
                    else if (p.Shape == "drone_empty_safe"){
                        this.drawImage(images[0], p.x, p.y, p.scale, p.text, p.text_color)
                    }
                    else if (p.Shape == "drone_filled_safe"){
                        this.drawImage(images[1], p.x, p.y, p.scale, p.text, p.text_color)
                    }
                    else if (p.Shape == "drone_empty_fast"){
                        this.drawImage(images[2], p.x, p.y, p.scale, p.text, p.text_color)
                    }
                    else if (p.Shape == "drone_filled_fast"){
                        this.drawImage(images[3], p.x, p.y, p.scale, p.text, p.text_color)
                    }
                    else if (p.Shape == "car_empty_safe"){
                        this.drawImage(images[4], p.x, p.y, p.scale, p.text, p.text_color)
                    }
                    else if (p.Shape == "car_filled_safe"){
                        this.drawImage(images[5], p.x, p.y, p.scale, p.text, p.text_color)
                    }
                    else if (p.Shape == "car_empty_fast"){
                        this.drawImage(images[6], p.x, p.y, p.scale, p.text, p.text_color)
                    }
                    else if (p.Shape == "car_filled_fast"){
                        this.drawImage(images[7], p.x, p.y, p.scale, p.text, p.text_color)
                    }
                    else
                        this.drawHospital(p.Shape, p.x, p.y, p.w, p.h, p.matrixIndex, p.Suppliers)
                        
            }
            // if a handler exists, update its mouse listeners with the new data
            (interactionHandler) ? interactionHandler.updateMouseListeners(portrayalLayer): null;
    };

    // DRAWING METHODS
    // =====================================================================

    /**
    Draw a circle in the specified grid cell.
    x, y: Grid coords
    r: Radius, as a multiple of cell size
    colors: List of colors for the gradient. Providing only one color will fill the shape with only that color, not gradient.
    stroke_color: Color to stroke the shape
    fill: Boolean for whether or not to fill the circle.
    text: Inscribed text in rectangle.
    text_color: Color of the inscribed text.
    */
    this.drawCircle = function(x, y, radius, colors, stroke_color, fill, text, text_color) {
            var cx = (x + 0.5) * cellWidth;
            var cy = (y + 0.5) * cellHeight;
            var r = radius * maxR;

            context.beginPath();
            context.arc(cx, cy, r, 0, Math.PI * 2, false);
            context.closePath();

            context.strokeStyle = stroke_color;
            context.stroke();

            if (fill) {
                    var gradient = context.createRadialGradient(cx, cy, r, cx, cy, 0);

                    for (i = 0; i < colors.length; i++) {
                            gradient.addColorStop(i/colors.length, colors[i]);
                    }

                    context.fillStyle = gradient;
                    context.fill();
            }

            // This part draws the text inside the Circle
            if (text !== undefined) {
                    context.fillStyle = text_color;
                    context.textAlign = 'center';
                    context.textBaseline= 'middle';
                    context.fillText(text, cx, cy);
            }

    };

    /**
    Draw a rectangle in the specified grid cell.
    x, y: Grid coords
    w, h: Width and height, [0, 1]
    colors: List of colors for the gradient. Providing only one color will fill the shape with only that color, not gradient.
    stroke_color: Color to stroke the shape
    fill: Boolean, whether to fill or not.
    text: Inscribed text in rectangle.
    text_color: Color of the inscribed text.
    */
    this.drawRectangle = function(x, y, w, h, colors, stroke_color, fill, text, text_color) {

            context.beginPath();
            var dx = w * cellWidth;
            var dy = h * cellHeight;

            // Keep in the center of the cell:
            var x0 = (x + 0.5) * cellWidth - dx/2;
            var y0 = (y + 0.5) * cellHeight - dy/2;

            context.strokeStyle = stroke_color;
            context.strokeRect(x0, y0, dx, dy);

            if (fill) {
                    var gradient = context.createLinearGradient(x0, y0, x0 + cellWidth, y0 + cellHeight);

                    for (i = 0; i < colors.length; i++) {
                            gradient.addColorStop(i/colors.length, colors[i]);
                    }

                    // Fill with gradient
                    context.fillStyle = gradient;
                    context.fillRect(x0,y0,dx,dy);
            }
            else {
                    context.fillStyle = colors;
                    context.strokeRect(x0, y0, dx, dy);
            }
            // This part draws the text inside the Rectangle
            if (text !== undefined) {
                    var cx = (x + 0.5) * cellWidth;
                    var cy = (y + 0.5) * cellHeight;
                    context.fillStyle = text_color;
                    context.textAlign = 'center';
                    context.textBaseline= 'middle';
                    context.fillText(text, cx, cy);
            }
    };

    /**
    Draw an arrow head in the specified grid cell.
    x, y: Grid coords
    s: Scaling of the arrowHead with respect to cell size[0, 1]
    colors: List of colors for the gradient. Providing only one color will fill the shape with only that color, not gradient.
    stroke_color: Color to stroke the shape
    fill: Boolean, whether to fill or not.
    text: Inscribed text in shape.
    text_color: Color of the inscribed text.
    */
    this.drawArrowHead = function(x, y, heading_x, heading_y, scale, colors, stroke_color, fill, text, text_color) {
            var arrowR = maxR * scale;
            var cx = (x + 0.5) * cellWidth;
            var cy = (y + 0.5) * cellHeight;
            if (heading_x === 0 && heading_y === 1) {
                    p1_x = cx;
                    p1_y = cy - arrowR;
                    p2_x = cx - arrowR;
                    p2_y = cy + arrowR;
                    p3_x = cx;
                    p3_y = cy + 0.8*arrowR;
                    p4_x = cx + arrowR;
                    p4_y = cy + arrowR;
            }
            else if (heading_x === 1 && heading_y === 0) {
                    p1_x = cx + arrowR;
                    p1_y = cy;
                    p2_x = cx - arrowR;
                    p2_y = cy - arrowR;
                    p3_x = cx - 0.8*arrowR;
                    p3_y = cy;
                    p4_x = cx - arrowR;
                    p4_y = cy + arrowR;
            }
            else if (heading_x === 0 && heading_y === (-1)) {
                    p1_x = cx;
                    p1_y = cy + arrowR;
                    p2_x = cx - arrowR;
                    p2_y = cy - arrowR;
                    p3_x = cx;
                    p3_y = cy - 0.8*arrowR;
                    p4_x = cx + arrowR;
                    p4_y = cy - arrowR;
            }
            else if (heading_x === (-1) && heading_y === 0) {
                    p1_x = cx - arrowR;
                    p1_y = cy;
                    p2_x = cx + arrowR;
                    p2_y = cy - arrowR;
                    p3_x = cx + 0.8*arrowR;
                    p3_y = cy;
                    p4_x = cx + arrowR;
                    p4_y = cy + arrowR;
            }

            context.beginPath();
            context.moveTo(p1_x, p1_y);
            context.lineTo(p2_x, p2_y);
            context.lineTo(p3_x, p3_y);
            context.lineTo(p4_x, p4_y);
            context.closePath();

            context.strokeStyle = stroke_color;
            context.stroke();

            if (fill) {
                    var gradient = context.createLinearGradient(p1_x, p1_y, p3_x, p3_y);

                    for (i = 0; i < colors.length; i++) {
                            gradient.addColorStop(i/colors.length, colors[i]);
                    }

                    // Fill with gradient
                    context.fillStyle = gradient;
                    context.fill();
            }

            // This part draws the text inside the ArrowHead
            if (text !== undefined) {
                    var cx = (x + 0.5) * cellWidth;
                      var cy = (y + 0.5) * cellHeight;
                    context.fillStyle = text_color
                    context.textAlign = 'center';
                    context.textBaseline= 'middle';
                    context.fillText(text, cx, cy);
            }
    };

    this.drawHospital = function(colors, x, y, w,h, id, suppliers){
            
            context.beginPath();
            var dx = w * cellWidth;
            var dy = h * cellHeight;
            var boxWidth = dx / 4

            // Keep in the center of the cell:
            var x0 = (x + 0.5) * cellWidth - dx/2;
            var y0 = (y + 0.5) * cellHeight - dy/2;


            context.fillStyle = "LightSlateGray"
            context.fillRect(x0,y0,dx,dy);


            context.fillStyle = colors[0];
            context.fillRect(x0 + boxWidth/4, y0 + 0.2*dy, boxWidth, dy*0.6);

            context.fillStyle = colors[1];
            context.fillRect(x0 + 1.5 *boxWidth, y0 + 0.2*dy, boxWidth, dy*0.6);

            context.fillStyle = colors[2];
            context.fillRect(x0 + 2.75 *boxWidth, y0 + 0.2*dy, boxWidth, dy*0.6);
        
            if (id !== undefined) {

                var cx = (x + 0.5) * cellWidth;
                var cy = (y + 0.5) * cellHeight - 1.5* dy;
                context.font = 'bold 12px serif'
                context.fillStyle = 'Black';
                context.textAlign = 'center';
                context.textBaseline= 'middle';
                context.fillText(id, cx, cy);
        }

    }

    this.drawCustomImage = function (shape, x, y, scale, text, text_color_) {
            var img = new Image();
                    img.src = "local/".concat(shape);
            if (scale === undefined) {
                    var scale = 1
            }
            // Calculate coordinates so the image is always centered
            var dWidth = cellWidth * scale;
            var dHeight = cellHeight * scale;
            var cx = x * cellWidth + cellWidth / 2 - dWidth / 2;
            var cy = y * cellHeight + cellHeight / 2 - dHeight / 2;

            // Coordinates for the text
            var tx = (x + 0.5) * cellWidth;
            var ty = (y + 0.5) * cellHeight;


            img.onload = function() {
                    context.drawImage(img, cx, cy, dWidth, dHeight);
                    // This part draws the text on the image
                    if (text !== undefined) {
                            // ToDo: Fix fillStyle
                            // context.fillStyle = text_color;
                            context.textAlign = 'center';
                            context.textBaseline= 'middle';
                            context.fillText(text, tx, ty);
                    }
            }
    }

    this.drawBackground = function(img, width, height){
        context.drawImage(img, 0,0, width, height)
    }

    this.drawImage = function (img, x, y, scale, text, text_color_) {
        if (scale === undefined) {
                var scale = 1
        }
        // Calculate coordinates so the image is always centered
        var dWidth = cellWidth * scale;
        var dHeight = cellHeight * scale;
        var cx = x * cellWidth + cellWidth / 2 - dWidth / 2;
        var cy = y * cellHeight + cellHeight / 2 - dHeight / 2;

        // Coordinates for the text
        var tx = (x + 0.5) * cellWidth;
        var ty = (y + 0.5) * cellHeight;
        context.drawImage(img, cx, cy, dWidth, dHeight);
        // img.onload = function() {
        //         context.drawImage(img, cx, cy, dWidth, dHeight);
        //         // This part draws the text on the image
        //         if (text !== undefined) {
        //                 // ToDo: Fix fillStyle
        //                 // context.fillStyle = text_color;
        //                 context.textAlign = 'center';
        //                 context.textBaseline= 'middle';
        //                 context.fillText(text, tx, ty);
        //         }
        // }
}

    /**
    Draw Grid lines in the full gird
    */

    this.drawGridLines = function() {
            context.beginPath();
            context.strokeStyle = "#eee";
            maxX = cellWidth * gridWidth;
            maxY = cellHeight * gridHeight;

            // Draw horizontal grid lines:
            for(var y=0; y<=maxY; y+=cellHeight) {
                    context.moveTo(0, y+0.5);
                    context.lineTo(maxX, y+0.5);
            }

            for(var x=0; x<=maxX; x+= cellWidth) {
                    context.moveTo(x+0.5, 0);
                    context.lineTo(x+0.5, maxY);
            }

            context.stroke();
    };

    this.resetCanvas = function() {
            context.clearRect(0, 0, width, height);
            context.beginPath();
    };

};