$(function () {
    console.log('🚀 СКРОЛЛ АНИМАЦИЯ ЗАПУЩЕНА');
    
    const START_SCROLL = 3562; // Точка начала
    
    const $window = $(window);
    const $bg = $('.parallax-layer'); // фоновое изображение
    const $image = $('.item_1_img');
    const $text = $('.item_1_text');
    const $group = $('.paralax__group'); // вся группа
    
    console.log('🔍 Элементы найдены:', {
        фон: $bg.length,
        картинка: $image.length,
        текст: $text.length,
        группа: $group.length
    });
    
    // Настройки анимации
    const settings = {
        bgMaxY: 400,        // Фон опустится на 400px и остановится
        bgDuration: 600,    // Фон анимируется 600px скролла
        elementsMaxX: 800,  // Элементы сдвинутся на 800px влево
        elementsMaxY: 600,  // Элементы опустятся на 600px вниз
        elementsDuration: 1200 // Элементы анимируются 1200px скролла
    };
    
    $window.on('scroll', function() {
        const scrollTop = $(this).scrollTop();
        const scrollFromStart = scrollTop - START_SCROLL;
        
        // Если достигли точки начала
        if (scrollTop >= START_SCROLL && scrollFromStart >= 0) {
            
            // 1. АНИМАЦИЯ ФОНА (первые 600px скролла)
            if (scrollFromStart <= settings.bgDuration) {
                const bgProgress = scrollFromStart / settings.bgDuration;
                const bgMoveY = bgProgress * settings.bgMaxY;
                
                $bg.css({
                    'transform': `translateY(${bgMoveY}px)`,
                    'transition': 'transform 0.1s linear'
                });
                console.log('🏞️ Фон:', Math.round(bgMoveY) + 'px');
            } else {
                // Фон достиг конечной позиции
                $bg.css({
                    'transform': `translateY(${settings.bgMaxY}px)`,
                    'transition': 'transform 0.1s linear'
                });
            }
            
            // 2. АНИМАЦИЯ КАРТИНКИ И ТЕКСТА (1200px скролла)
            if (scrollFromStart <= settings.elementsDuration) {
                const elementsProgress = scrollFromStart / settings.elementsDuration;
                
                // Горизонтальное смещение (влево)
                const moveX = -elementsProgress * settings.elementsMaxX;
                
                // Вертикальное смещение (вниз)
                const moveY = elementsProgress * settings.elementsMaxY;
                
                // Картинка
                $image.css({
                    'transform': `translateX(${moveX}px) translateY(${moveY}px)`,
                    'transition': 'transform 0.1s linear',
                    'opacity': 1
                });
                
                // Текст (немного другие коэффициенты)
                $text.css({
                    'transform': `translateX(${moveX * 0.8}px) translateY(${moveY}px)`,
                    'transition': 'transform 0.1s linear',
                    'opacity': 1
                });
                
                console.log(`🎬 Элементы: X=${Math.round(moveX)}px, Y=${Math.round(moveY)}px`);
                
            } else {
                // Элементы достигли конечной позиции
                $image.css({
                    'transform': `translateX(${-settings.elementsMaxX}px) translateY(${settings.elementsMaxY}px)`,
                    'opacity': 1
                });
                
                $text.css({
                    'transform': `translateX(${-settings.elementsMaxX * 0.8}px) translateY(${settings.elementsMaxY}px)`,
                    'opacity': 1
                });
            }
            
            // 3. АНИМАЦИЯ ВСЕЙ ГРУППЫ (параллакс эффект)
            const groupMoveY = Math.min(scrollFromStart * 0.5, 300); // группа опускается медленнее
            $group.css({
                'transform': `translateY(${groupMoveY}px)`,
                'transition': 'transform 0.1s linear'
            });
            
        } else {
            // ДО анимации - сбрасываем позиции
            resetPositions();
        }
    });
    
    function resetPositions() {
        $bg.css({
            'transform': 'translateY(0px)',
            'transition': 'transform 0.3s ease-out'
        });
        
        $image.css({
            'transform': 'translateX(0px) translateY(0px)',
            'transition': 'transform 0.3s ease-out',
            'opacity': 0.5
        });
        
        $text.css({
            'transform': 'translateX(0px) translateY(0px)',
            'transition': 'transform 0.3s ease-out',
            'opacity': 0.5
        });
        
        $group.css({
            'transform': 'translateY(0px)',
            'transition': 'transform 0.3s ease-out'
        });
    }
    
    // Инициализация
    resetPositions();
    console.log('✅ Анимация готова. Скроллите вниз после ' + START_SCROLL + 'px');
    console.log('📊 Настройки:', settings);
});