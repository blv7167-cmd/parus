// ==================== МОДАЛЬНОЕ ОКНО ====================
(function() {
    let modal, formContainer, successContainer;
    
    function closeModal() {
        console.log('closeModal вызвана');
        if (modal) {
            modal.style.display = 'none';
            modal.style.opacity = '0';
        }
        document.body.style.overflow = '';
        
        const form = document.getElementById('callbackForm');
        if (form) form.reset();
        if (formContainer) formContainer.style.display = 'block';
        if (successContainer) successContainer.classList.remove('show');
        
        const submitBtn = form ? form.querySelector('button[type="submit"]') : null;
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Отправить заявку';
        }
    }
    
    function openModal(event) {
        if (event) event.preventDefault();
        console.log('openModal вызвана');
        if (modal) {
            modal.style.display = 'flex';
            modal.style.opacity = '1';
        }
        document.body.style.overflow = 'hidden';
    }
    
    // Функция для привязки кнопки закрытия (будет вызываться несколько раз)
    function bindSuccessCloseButton() {
        const successCloseBtn = document.getElementById('successClose');
        if (successCloseBtn) {
            console.log('Привязываем кнопку successClose (прямая привязка)');
            // Убираем все старые обработчики
            const newBtn = successCloseBtn.cloneNode(true);
            successCloseBtn.parentNode.replaceChild(newBtn, successCloseBtn);
            // Привязываем новый обработчик
            newBtn.onclick = function(e) {
                e.preventDefault();
                e.stopPropagation();
                console.log('Кнопка Закрыть нажата!');
                closeModal();
                return false;
            };
            // Добавляем также атрибут для надёжности
            newBtn.setAttribute('data-close-modal', 'true');
        } else {
            console.log('Кнопка successClose не найдена, повторная попытка через 100ms');
            setTimeout(bindSuccessCloseButton, 100);
        }
    }
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    function init() {
        console.log('Инициализация модального окна');
        
        modal = document.getElementById('callbackModal');
        const openBtn = document.getElementById('openModalBtn');
        const closeBtn = document.getElementById('modalClose');
        formContainer = document.getElementById('modalForm');
        successContainer = document.getElementById('modalSuccess');
        const form = document.getElementById('callbackForm');
        
        if (!modal) {
            console.error('Модальное окно не найдено!');
            return;
        }
        
        if (!openBtn) {
            console.error('Кнопка openModalBtn не найдена!');
            return;
        }
        
        openBtn.onclick = openModal;
        if (closeBtn) closeBtn.onclick = closeModal;
        
        modal.onclick = function(event) {
            if (event.target === modal) closeModal();
        };
        
        document.onkeydown = function(event) {
            if (event.key === 'Escape' && modal.style.display === 'flex') closeModal();
        };
        
        // Первая привязка кнопки закрытия
        bindSuccessCloseButton();
        
        if (form) {
            form.onsubmit = async function(event) {
                event.preventDefault();
                console.log('Отправка формы');
                
                const name = document.getElementById('userName')?.value.trim() || '';
                const phone = document.getElementById('userPhone')?.value.trim() || '';
                const question = document.getElementById('userQuestion')?.value.trim() || '';
                
                if (!phone) {
                    alert('Пожалуйста, введите номер телефона');
                    return;
                }
                
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn) {
                    submitBtn.disabled = true;
                    submitBtn.textContent = 'Отправка...';
                }
                
                const formData = new URLSearchParams();
                formData.append('name', name || 'Не указано');
                formData.append('phone', phone);
                formData.append('question', question || '');
                formData.append('page', window.location.pathname || 'about.html');
                formData.append('timestamp', new Date().toISOString());
                
                try {
                    await fetch('/send_message', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                        body: formData.toString()
                    });
                } catch (error) {
                    console.error('Ошибка:', error);
                }
                
                if (formContainer) formContainer.style.display = 'none';
                if (successContainer) successContainer.classList.add('show');
                if (submitBtn) submitBtn.disabled = false;
                
                // После показа success-блока привязываем кнопку снова
                setTimeout(bindSuccessCloseButton, 50);
            };
        }
        
        console.log('Модальное окно готово');
    }
})();

// ==================== COOKIE БАННЕР ====================
(function() {
    function setCookie(name, value, days) {
        const date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        document.cookie = name + "=" + (value || "") + "; expires=" + date.toUTCString() + "; path=/";
    }

    function getCookie(name) {
        const nameEQ = name + "=";
        const ca = document.cookie.split(';');
        for (let i = 0; i < ca.length; i++) {
            let c = ca[i];
            while (c.charAt(0) === ' ') c = c.substring(1, c.length);
            if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
        }
        return null;
    }

    function hideBanner() {
        const banner = document.getElementById('cookieBanner');
        if (banner) banner.classList.remove('show');
    }

    function checkCookieConsent() {
        const consent = getCookie('cookie_consent');
        if (consent === 'accepted' || consent === 'declined') {
            hideBanner();
        } else {
            const banner = document.getElementById('cookieBanner');
            if (banner) setTimeout(() => banner.classList.add('show'), 500);
        }
    }

    function acceptCookies() {
        setCookie('cookie_consent', 'accepted', 365);
        hideBanner();
    }

    function declineCookies() {
        setCookie('cookie_consent', 'declined', 365);
        hideBanner();
    }

    document.addEventListener('DOMContentLoaded', function() {
        checkCookieConsent();

        const acceptBtn = document.getElementById('cookieAccept');
        const declineBtn = document.getElementById('cookieDecline');
        if (acceptBtn) acceptBtn.addEventListener('click', acceptCookies);
        if (declineBtn) declineBtn.addEventListener('click', declineCookies);
    });
})();

// ==================== ОТПРАВКА ФОРМЫ ОТЗЫВОВ ====================
(function() {
    function initReviewForm() {
        const reviewForm = document.getElementById('review-form');
        const reviewSuccess = document.getElementById('review-success');
        if (!reviewForm || !reviewSuccess) return;

        reviewForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const name = document.getElementById('review-name')?.value.trim() || '';
            const contact = document.getElementById('review-contact')?.value.trim() || '';
            const role = document.getElementById('review-role')?.value || '';
            const rating = document.getElementById('review-rating')?.value || '';
            const message = document.getElementById('review-text')?.value.trim() || '';
            const consent = document.getElementById('review-consent')?.checked || false;

            if (!name || !message || !rating || !consent) {
                alert('Пожалуйста, заполните все обязательные поля');
                return;
            }

            const submitBtn = reviewForm.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Отправка...';
            }

            const formData = new URLSearchParams();
            formData.append('name', name);
            formData.append('contact', contact);
            formData.append('role', role);
            formData.append('rating', rating);
            formData.append('message', message);
            formData.append('page', window.location.pathname);
            formData.append('timestamp', new Date().toISOString());

            try {
                await fetch('/send_review', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: formData.toString()
                });
            } catch (error) {
                console.error('Ошибка отправки отзыва:', error);
            }

            reviewSuccess.classList.remove('hidden');
            reviewForm.reset();
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Отправить отзыв';
            }
            setTimeout(() => reviewSuccess.classList.add('hidden'), 5000);
        });
    }

    document.addEventListener('DOMContentLoaded', initReviewForm);
})();

// ==================== ЛАЙТБОКС ====================
(function() {
    function initLightbox() {
        const lightbox = document.getElementById('lightbox');
        const lightboxImg = document.getElementById('lightbox-img');
        const caption = document.getElementById('lightbox-caption');
        if (!lightbox || !lightboxImg) return;

        const closeBtn = lightbox.querySelector('.lightbox__close');
        const triggers = document.querySelectorAll('[data-lightbox-src]');

        function openLightbox(src, title) {
            lightboxImg.src = src;
            if (caption) caption.innerHTML = (title || '').replace(/\n/g, '<br>');
            lightbox.classList.remove('hidden');
            document.body.style.overflow = 'hidden';
            if (closeBtn) closeBtn.focus();
        }

        function closeLightbox() {
            lightbox.classList.add('hidden');
            lightboxImg.src = '';
            if (caption) caption.innerHTML = '';
            document.body.style.overflow = '';
        }

        triggers.forEach(el => {
            el.addEventListener('click', () => {
                openLightbox(el.getAttribute('data-lightbox-src'), el.getAttribute('data-title'));
            });
        });

        if (closeBtn) closeBtn.addEventListener('click', closeLightbox);
        lightbox.addEventListener('click', (e) => { if (e.target === lightbox) closeLightbox(); });
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !lightbox.classList.contains('hidden')) closeLightbox();
        });
    }

    document.addEventListener('DOMContentLoaded', initLightbox);
})();

// ==================== УПРАВЛЕНИЕ ACTION BAR ====================
(function() {
    function initActionBar() {
        const actionBar = document.querySelector('.fixed-action-bar');
        if (!actionBar) return;

        let lastScrollTop = 0;
        window.addEventListener('scroll', () => {
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            if (scrollTop > lastScrollTop && scrollTop > 100) {
                actionBar.classList.add('hide');
            } else {
                actionBar.classList.remove('hide');
            }
            lastScrollTop = scrollTop;
        });
    }

    document.addEventListener('DOMContentLoaded', initActionBar);
})();