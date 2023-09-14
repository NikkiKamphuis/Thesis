var CustomCanvasModule = function(canvas_width, canvas_height, grid_width, grid_height) {
	// Create the element
	// ------------------
	
	// Create the tag with absolute positioning :
	var canvas_tag = `<canvas width="${canvas_width}" height="${canvas_height}" class="world-grid"/>`
	var parent_div_tag = '<div style="height:' + canvas_height + 'px;" class="world-grid-parent"></div>'
	// var canvas_tag = `<canvas width=100%; height=100%;" class="world-grid"/>`
	// var parent_div_tag = '<div style="height:100%;" class="world-grid-parent"></div>'

	// Append it to body:
	var canvas = $(canvas_tag)[0];
	var interaction_canvas = $(canvas_tag)[0];
	var parent = $(parent_div_tag)[0];

	//var imageLetters = ['g','y','r']

	//$("body").append(canvas);
	$("#elements").append(parent);
	parent.append(canvas);
	parent.append(interaction_canvas);

	// Create the context for the agents and interactions and the drawing controller:
	var context = canvas.getContext("2d");

	// Create an interaction handler using the
	var interactionHandler = new CustomInteractionHandler(canvas_width, canvas_height, grid_width, grid_height, interaction_canvas.getContext("2d"));
	var canvasDraw = new CustomGridVisualization(canvas_width, canvas_height, grid_width, grid_height, context, interactionHandler);
	
	var images = ['100_drone_empty_safe.png',
	'100_drone_filled_safe.png',
	'100_drone_empty_fast.png',
	'100_drone_filled_fast.png',
	'100_car_empty_safe.png',
	'100_car_filled_safe.png',
	'100_car_empty_fast.png',
	'100_car_filled_fast.png',
	'backGroundMap.jpg'];
	// for (const color1 of imageLetters){
	// 	for (const color2 of imageLetters){
	// 		for (const color3 of imageLetters){
	// 			fileName = 'visualization/hospitals/'+color1 + color2 + color3+'-min.png'
	// 			images.push(fileName)
	// 		}
	// 	}
	// }

	var loc = window.location.pathname;
	var dir = loc.substring(0, loc.lastIndexOf('/'));

	console.log(loc)
	console.log(dir)

    var loadedImages = new Array();
    for (let i=0;i<images.length;i++){
		console.log(images[i])
		loadedImages[i] = new Image();
        //loadedImages[i].src = "local/pictures/".concat(images[i]);
		loadedImages[i].src = "/static/pictures/".concat(images[i]);
	}
	



	console.log(loadedImages[4])
	
	this.render = function(data) {

		canvasDraw.resetCanvas();
		canvasDraw.drawBackground(loadedImages[8],canvas_width, canvas_height)
		for (var layer in data)
			
			canvasDraw.drawLayer(data[layer], loadedImages);
        //uncomment if grid lines are nessacerry
		//canvasDraw.drawGridLines("#eee");   
	};

	this.reset = function() {
		canvasDraw.resetCanvas();
	};

};