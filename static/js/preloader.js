function preloadImages(urls, allImagesLoadedCallback) {
    let loadedCounter = 0;
    const toBeLoadedNumber = urls.length;
    const progressBar = document.querySelector('.preloader .progress .progress-value');

    function preloadImage(url, callback) {
        const img = new Image();
        img.onload = callback;
        img.onerror = callback;               // ← важно! чтобы 404 не стопал прелоадер
        img.src = url;
    }

    urls.forEach(url => {
        preloadImage(url, () => {
            loadedCounter++;
            const loadedPercent = Math.round((loadedCounter / toBeLoadedNumber) * 100);
            console.log('[App Info] loading ' + loadedPercent + '%...');
            if (progressBar) progressBar.style.width = loadedPercent + '%';

            if (loadedCounter === toBeLoadedNumber) {
                allImagesLoadedCallback();
            }
        });
    });
}

// Запуск
if (window.preloadImagesList && window.preloadImagesList.length > 0) {
    preloadImages(window.preloadImagesList, function() {
        console.log('[App Info] loading completed.');
        document.body.classList.add('loaded');
    });
} else {
    console.warn('[App Info] No preload images defined');
    document.body.classList.add('loaded');  // чтобы не висело вечно
}