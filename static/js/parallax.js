function elementReady(selector) {
    return new Promise((resolve, reject) => {
        const el = document.querySelector(selector);
        if (el) {
            resolve(el);
        }

        new MutationObserver((mutationRecords, observer) => {
            Array.from(document.querySelectorAll(selector)).forEach(element => {
                resolve(element);
                observer.disconnect();
            });
        })
        .observe(document.documentElement, {
            childList: true,
            subtree: true
        });
    });
}

var screenH = Math.max(window.screen.height, window.innerHeight);
var marginV = Math.round(screenH / 3);
window.onresize = function(){
    screenH = Math.max(window.screen.height, window.innerHeight);
    marginV = Math.round(screenH / 4);
}
Promise.all([
    elementReady("#group1 .parallax-layer--back-0"),
    elementReady("#group1 .parallax-layer--back-1"),
    elementReady("#group1 .parallax-layer--back-2"),
    elementReady("#group1 .parallax-layer--back-3"),
]).then(() => {
    window.onresize = window.onscroll = function(){
        var scrollY = Math.max(window.scrollY, window.pageYOffset);
        if (scrollY < (screenH / 2)) {
            if (scrollY > 0) {
                var ratioScrollScreen = scrollY/screenH;
            } else {
                var ratioScrollScreen = 0;
            }
            var marginBack0 = Math.round(-1 * ratioScrollScreen * marginV * 0.75);
            var marginBack1 = Math.round(ratioScrollScreen * marginV * 1.75);
            var marginBack2 = Math.round(-1 * ratioScrollScreen * marginV * 0.5);
            document.querySelector("#group1 .parallax-layer--back-0").style.marginTop=`${marginBack0}px`;
            document.querySelector("#group1 .parallax-layer--back-1").style.marginTop=`${marginBack1}px`;
            document.querySelector("#group1 .parallax-layer--back-2").style.marginTop=`${marginBack2}px`;
        }
    }
});