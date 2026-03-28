// Функция для установки cookie
function setCookie(name, value, days) {
    const date = new Date();
    date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
    const expires = "; expires=" + date.toUTCString();
    document.cookie = name + "=" + (value || "") + expires + "; path=/";
}

// Функция для получения cookie
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

// Функция для скрытия баннера
function hideBanner() {
    const banner = document.getElementById('cookieBanner');
    if (banner) {
        banner.classList.remove('show');
    }
}

// Проверка, было ли уже принято решение о cookie
function checkCookieConsent() {
    const consent = getCookie('cookie_consent');
    if (consent === 'accepted' || consent === 'declined') {
        hideBanner();
    } else {
        const banner = document.getElementById('cookieBanner');
        if (banner) {
            banner.classList.add('show');
        }
        setTimeout(() => {
            const banner = document.getElementById('cookieBanner');
            if (banner) {
                banner.classList.add('show');
            }
        }, 500);
    }
}

// Обработчик принятия cookie
function acceptCookies() {
    setCookie('cookie_consent', 'accepted', 365);
    hideBanner();
    console.log('Cookies accepted');
}

// Обработчик отклонения cookie
function declineCookies() {
    setCookie('cookie_consent', 'declined', 365);
    hideBanner();
    console.log('Cookies declined');
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function () {
    checkCookieConsent();

    const acceptBtn = document.getElementById('cookieAccept');
    const declineBtn = document.getElementById('cookieDecline');

    if (acceptBtn) {
        acceptBtn.addEventListener('click', acceptCookies);
    }
    if (declineBtn) {
        declineBtn.addEventListener('click', declineCookies);
    }
});
