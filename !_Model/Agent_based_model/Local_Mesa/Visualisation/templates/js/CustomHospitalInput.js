var HistogramModule = function(Hospitals) {
	// Create the elements
	
	// Create the tag:
	var canvas_tag = "<canvas width='" + canvas_width + "' height='" + canvas_height + "' ";
	canvas_tag += "style='border:1px dotted'></canvas>";
	// Append it to body:
	var canvas = $(canvas_tag)[0];
	$("body").append(canvas);
	// Create the context and the drawing controller:
	var context = canvas.getContext("2d");



	for (const hospital of Hospitals){

	}
		

	var data = {
		labels: bins,
		datasets: datasets
	};

	var options = {
		scaleBeginsAtZero: true
	};

	var chart = new Chart(context).Bar(data, options);

	this.render = function(data) {
		for (var i in data)
			chart.datasets[0].bars[i].value = data[i];
		chart.update();
	};

	this.reset = function() {
		chart.destroy();
		chart = new Chart(context).Bar(data, options);
	};
};