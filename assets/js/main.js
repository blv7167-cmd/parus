(function() {
    // Переменная для хранения экземпляра капчи
    var captchaInstance = null;
    
    // Инициализация Yandex SmartCaptcha
    function initSmartCaptcha() {
        // Проверяем, что контейнер существует и капча ещё не инициализирована
        var container = document.getElementById('captcha-container');
        if (!container) {
            console.log('Контейнер капчи не найден');
            return false;
        }
        
        // Проверяем, что библиотека загрузилась
        if (typeof window.smartCaptcha === 'undefined') {
            console.log('SmartCaptcha не загружена, ждём...');
            return false;
        }
        
        // Если уже инициализирована, не делаем повторно
        if (captchaInstance) {
            console.log('Капча уже инициализирована');
            return true;
        }
        
        try {
            captchaInstance = window.smartCaptcha.render(container, {
                sitekey: 'ysc1_PGmulRYuGEEEIUU29qpRC3vTyQg1fvOgbSu428yx0097a33c',  // Замените на ваш ключ Yandex
                callback: function(token) {
                    console.log('Капча пройдена, токен получен');
                    document.getElementById('smart-token').value = token;
                },
                expiredCallback: function() {
                    console.log('Капча просрочена');
                    document.getElementById('smart-token').value = '';
                }
            });
            console.log('SmartCaptcha инициализирована');
            return true;
        } catch(e) {
            console.error('Ошибка инициализации SmartCaptcha:', e);
            return false;
        }
    }
    
    // Функция ожидания загрузки библиотеки SmartCaptcha
    function waitForSmartCaptcha(callback, maxAttempts = 30) {
        var attempts = 0;
        
        function check() {
            if (typeof window.smartCaptcha !== 'undefined' && typeof window.smartCaptcha.render === 'function') {
                console.log('SmartCaptcha библиотека загружена');
                callback();
            } else if (attempts < maxAttempts) {
                attempts++;
                console.log('Ждём загрузку SmartCaptcha, попытка ' + attempts);
                setTimeout(check, 200);
            } else {
                console.error('SmartCaptcha не загрузилась за отведённое время');
            }
        }
        
        check();
    }
    
    // Инициализация модального окна
    function initModal() {
        var modal = document.getElementById('callbackModal');
        var btns = document.querySelectorAll('.open-modal-btn');
        var closeBtn = document.getElementById('modalClose');
        var form = document.getElementById('callbackForm');
        var formContainer = document.getElementById('modalForm');
        var successContainer = document.getElementById('modalSuccess');
        var successClose = document.getElementById('successClose');
        
        if (!modal) {
            console.log('Модальное окно не найдено, повторная попытка через 500ms');
            setTimeout(initModal, 500);
            return;
        }
        
        console.log('Модальное окно найдено, кнопок:', btns.length);
        
        function openModal(e) {
            if (e) e.preventDefault();
            modal.classList.add('show');
            document.body.style.overflow = 'hidden';
            
            // При открытии окна инициализируем капчу
            waitForSmartCaptcha(function() {
                var inited = initSmartCaptcha();
                if (!inited) {
                    console.log('Не удалось инициализировать капчу, пробуем сбросить и пересоздать');
                    // Сбрасываем старый экземпляр и пробуем снова
                    captchaInstance = null;
                    setTimeout(initSmartCaptcha, 500);
                }
            });
            
            console.log('Модальное окно открыто');
        }
        
        function closeModal() {
            modal.classList.remove('show');
            document.body.style.overflow = '';
            if (form) form.reset();
            if (formContainer) formContainer.style.display = 'block';
            if (successContainer) successContainer.classList.remove('show');
            // Очищаем токен при закрытии
            document.getElementById('smart-token').value = '';
            console.log('Модальное окно закрыто');
        }
        
        function handleSubmit(e) {
            e.preventDefault();
            
            var captchaToken = document.getElementById('smart-token').value;
            if (!captchaToken) {
                alert('Пожалуйста, подтвердите, что вы не робот');
                return;
            }
            
            var phone = document.getElementById('userPhone')?.value.trim();
            if (!phone) {
                alert('Пожалуйста, введите номер телефона');
                return;
            }
            
            var submitBtn = e.target.querySelector('button[type="submit"]');
            var originalText = submitBtn.innerText;
            submitBtn.innerText = 'Отправка...';
            submitBtn.disabled = true;
            
            console.log('Отправка заявки, телефон:', phone);
            
            if (formContainer) formContainer.style.display = 'none';
            if (successContainer) successContainer.classList.add('show');
            
            var formData = new URLSearchParams();
            formData.append('name', document.getElementById('userName')?.value.trim() || '');
            formData.append('phone', phone);
            formData.append('question', document.getElementById('userQuestion')?.value.trim() || '');
            formData.append('page', window.location.pathname);
            formData.append('timestamp', new Date().toISOString());
            formData.append('smart-token', captchaToken);
            
            fetch('/send_message', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: formData.toString()
            })
            .then(function(response) {
                return response.json();
            })
            .then(function(data) {
                if (data.status === 'success') {
                    console.log('Заявка успешно отправлена');
                } else {
                    alert('Ошибка: ' + data.message);
                    if (formContainer) formContainer.style.display = 'block';
                    if (successContainer) successContainer.classList.remove('show');
                    // Сбрасываем капчу при ошибке
                    if (captchaInstance && window.smartCaptcha) {
                        window.smartCaptcha.reset(captchaInstance);
                    }
                    document.getElementById('smart-token').value = '';
                }
            })
            .catch(function(error) {
                console.error('Ошибка отправки:', error);
                alert('Произошла ошибка. Пожалуйста, попробуйте позже.');
                if (formContainer) formContainer.style.display = 'block';
                if (successContainer) successContainer.classList.remove('show');
                if (captchaInstance && window.smartCaptcha) {
                    window.smartCaptcha.reset(captchaInstance);
                }
                document.getElementById('smart-token').value = '';
            })
            .finally(function() {
                submitBtn.innerText = originalText;
                submitBtn.disabled = false;
            });
        }
        
        for (var i = 0; i < btns.length; i++) {
            btns[i].onclick = openModal;
        }
        
        if (closeBtn) closeBtn.onclick = closeModal;
        if (successClose) successClose.onclick = closeModal;
        if (form) form.onsubmit = handleSubmit;
        
        modal.onclick = function(e) {
            if (e.target === modal) closeModal();
        };
        
        document.onkeydown = function(e) {
            if (e.key === 'Escape' && modal.classList.contains('show')) closeModal();
        };
    }
    
    // Cookie баннер
    function initCookieBanner() {
        var banner = document.getElementById('cookieBanner');
        var acceptBtn = document.getElementById('cookieAccept');
        var declineBtn = document.getElementById('cookieDecline');
        
        if (!banner) {
            setTimeout(initCookieBanner, 500);
            return;
        }
        
        var consent = localStorage.getItem('cookieConsent');
        
        if (!consent) {
            banner.classList.add('show');
        }
        
        function setConsent(accepted) {
            localStorage.setItem('cookieConsent', accepted ? 'accepted' : 'declined');
            banner.classList.remove('show');
        }
        
        if (acceptBtn) acceptBtn.onclick = function() { setConsent(true); };
        if (declineBtn) declineBtn.onclick = function() { setConsent(false); };
    }
    
    // Форма отзывов
    function initReviewForm() {
        var reviewForm = document.getElementById('review-form');
        var reviewSuccess = document.getElementById('review-success');
        if (!reviewForm || !reviewSuccess) return;
        
        reviewForm.onsubmit = function(e) {
            e.preventDefault();
            if (!reviewForm.checkValidity()) {
                reviewForm.reportValidity();
                return;
            }
            reviewSuccess.classList.remove('hidden');
            reviewForm.reset();
            setTimeout(function() {
                reviewSuccess.classList.add('hidden');
            }, 5000);
        };
    }
    
    // Action bar
    function initActionBar() {
        var actionBar = document.querySelector('.fixed-action-bar');
        if (!actionBar) return;
        var lastScrollTop = 0;
        window.onscroll = function() {
            var scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            if (scrollTop > lastScrollTop && scrollTop > 100) {
                actionBar.classList.add('hide');
            } else {
                actionBar.classList.remove('hide');
            }
            lastScrollTop = scrollTop;
        };
    }
    
    // Загрузка компонентов
    async function loadComponent(elementId, url) {
        try {
            const response = await fetch(url);
            const html = await response.text();
            document.getElementById(elementId).innerHTML = html;
            console.log('Загружен компонент:', url);
            return true;
        } catch (error) {
            console.error('Ошибка загрузки ' + url + ':', error);
            return false;
        }
    }
    
    // Старт
    document.addEventListener('DOMContentLoaded', function() {
        Promise.all([
            loadComponent('header', 'assets/components/header.html'),
            loadComponent('footer', 'assets/components/footer.html'),
            loadComponent('actionBar', 'assets/components/action-bar.html'),
            loadComponent('cookieBanner', 'assets/components/cookie-banner.html'),
            loadComponent('callbackModal', 'assets/components/modal.html')
        ]).then(function() {
            console.log('Все компоненты загружены, запускаем инициализацию');
            initModal();
            initCookieBanner();
            initReviewForm();
            initActionBar();
            
            // Предварительная загрузка капчи (не рендерим, просто убеждаемся, что библиотека готова)
            waitForSmartCaptcha(function() {
                console.log('SmartCaptcha библиотека готова для использования');
            });
        }).catch(function(error) {
            console.error('Ошибка при загрузке компонентов:', error);
        });
    });
})();