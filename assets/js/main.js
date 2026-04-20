(function() {
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
            console.log('Модальное окно открыто');
        }
        
        function closeModal() {
            modal.classList.remove('show');
            document.body.style.overflow = '';
            if (form) form.reset();
            if (formContainer) formContainer.style.display = 'block';
            if (successContainer) successContainer.classList.remove('show');
            console.log('Модальное окно закрыто');
        }
        
        function handleSubmit(e) {
            e.preventDefault();
            var phone = document.getElementById('userPhone')?.value.trim();
            if (!phone) {
                alert('Пожалуйста, введите номер телефона');
                return;
            }
            console.log('Отправка заявки, телефон:', phone);
            if (formContainer) formContainer.style.display = 'none';
            if (successContainer) successContainer.classList.add('show');
            
            var formData = new URLSearchParams();
            formData.append('name', document.getElementById('userName')?.value.trim() || '');
            formData.append('phone', phone);
            formData.append('question', document.getElementById('userQuestion')?.value.trim() || '');
            formData.append('page', window.location.pathname);
            formData.append('timestamp', new Date().toISOString());
            
            fetch('/send_message', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: formData.toString()
            }).catch(function(error) {
                console.error('Ошибка отправки:', error);
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
    
    // Cookie баннер — ИСПРАВЛЕННАЯ ВЕРСИЯ
    function initCookieBanner() {
        var banner = document.getElementById('cookieBanner');
        var acceptBtn = document.getElementById('cookieAccept');
        var declineBtn = document.getElementById('cookieDecline');
        
        console.log('initCookieBanner вызван, banner:', !!banner);
        console.log('acceptBtn:', !!acceptBtn, 'declineBtn:', !!declineBtn);
        
        if (!banner) {
            console.log('Баннер не найден, повторная попытка через 500ms');
            setTimeout(initCookieBanner, 500);
            return;
        }
        
        // Проверяем, есть ли сохранённое согласие
        var consent = localStorage.getItem('cookieConsent');
        console.log('Сохранённое согласие:', consent);
        
        if (!consent) {
            console.log('Показываем баннер');
            banner.classList.add('show');
        } else {
            console.log('Баннер не показываем, уже есть согласие');
        }
        
        function setConsent(accepted) {
            localStorage.setItem('cookieConsent', accepted ? 'accepted' : 'declined');
            banner.classList.remove('show');
            console.log('Согласие установлено:', accepted ? 'accepted' : 'declined');
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
    
    // Action bar скрытие при скролле
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
    
    // Старт после загрузки DOM
    document.addEventListener('DOMContentLoaded', function() {
        // Загружаем все компоненты и ждём их полной загрузки
        Promise.all([
            loadComponent('header', 'assets/components/header.html'),
            loadComponent('footer', 'assets/components/footer.html'),
            loadComponent('actionBar', 'assets/components/action-bar.html'),
            loadComponent('cookieBanner', 'assets/components/cookie-banner.html'),
            loadComponent('callbackModal', 'assets/components/modal.html')
        ]).then(function() {
            console.log('Все компоненты загружены, запускаем инициализацию');
            // Теперь все компоненты точно в DOM
            initModal();
            initCookieBanner();
            initReviewForm();
            initActionBar();
        }).catch(function(error) {
            console.error('Ошибка при загрузке компонентов:', error);
        });
    });
})();