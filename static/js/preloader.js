function preloadImages(urls, allImagesLoadedCallback){
    var loadedCounter = 0;
	var toBeLoadedNumber = urls.length;
	var progressBar = document.querySelector('.preloader .progress .progress-value');
	urls.forEach(function(url){
		preloadImage(url, function(){
			loadedCounter++;
			loadedPercent = Math.round(loadedCounter/toBeLoadedNumber*100);
			console.log('[App Info] loading ' + loadedPercent + '%...');
			progressBar.style.width = loadedPercent + '%';
			if(loadedCounter == toBeLoadedNumber){
				allImagesLoadedCallback();
			}
		});
	});
	function preloadImage(url, anImageLoadedCallback){
		var img = new Image();
		img.onload = anImageLoadedCallback;
		img.src = url;
	}
}

preloadImages([
	'img/whale_1.png',
	'img/whale_2.png',
    'img/whale_3.png',
	'img/stingray.jpg',
], function(){
    console.log('[App Info] loading completed.');
    document.body.classList.add('loaded');
});