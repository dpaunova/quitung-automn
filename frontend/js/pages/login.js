/**
 * Login page.
 */
var LoginPage = (function() {
    function render(container) {
        container.innerHTML = '\
        <div class="auth-page">\
            <div class="auth-card">\
                <div class="auth-logo">\
                    <span class="logo-icon">📄</span>\
                    <span class="logo-text">Beleg Scanner</span>\
                </div>\
                <div id="login-error" class="alert alert-danger hidden"></div>\
                <form id="login-form">\
                    <div class="form-group">\
                        <label class="form-label" for="login-email">Имейл</label>\
                        <input class="form-input" id="login-email" type="email"\
                               placeholder="ime@firma.bg" required autocomplete="email">\
                    </div>\
                    <div class="form-group">\
                        <label class="form-label" for="login-password">Парола</label>\
                        <input class="form-input" id="login-password" type="password"\
                               placeholder="Въведете парола" required autocomplete="current-password">\
                    </div>\
                    <button type="submit" class="btn btn-primary btn-block btn-lg">Вход</button>\
                </form>\
                <div class="auth-footer">\
                    Нямате акаунт? <a href="#/register">Регистрация</a>\
                </div>\
            </div>\
        </div>';

        var form = document.getElementById('login-form');
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            var email = document.getElementById('login-email').value.trim();
            var password = document.getElementById('login-password').value;
            var errorEl = document.getElementById('login-error');
            var btn = form.querySelector('button[type="submit"]');

            errorEl.classList.add('hidden');
            btn.disabled = true;
            btn.textContent = 'Влизане...';

            API.login(email, password)
                .then(function() {
                    window.location.hash = '#/';
                })
                .catch(function(err) {
                    errorEl.textContent = err.message || 'Грешка при вход';
                    errorEl.classList.remove('hidden');
                    btn.disabled = false;
                    btn.textContent = 'Вход';
                });
        });
    }

    return { render: render };
})();
