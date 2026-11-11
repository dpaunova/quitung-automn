/**
 * Register page.
 */
var RegisterPage = (function() {
    function render(container) {
        container.innerHTML = '\
        <div class="auth-page">\
            <div class="auth-card">\
                <div class="auth-logo">\
                    <span class="logo-icon">📄</span>\
                    <span class="logo-text">Beleg Scanner</span>\
                </div>\
                <div id="reg-error" class="alert alert-danger hidden"></div>\
                <form id="register-form">\
                    <div class="section-title">Данни за фирмата</div>\
                    <div class="form-group">\
                        <label class="form-label" for="reg-biz-name">Име на фирмата</label>\
                        <input class="form-input" id="reg-biz-name" type="text"\
                               placeholder="ООД / ЕООД / ЕТ..." required>\
                    </div>\
                    <div class="form-group">\
                        <label class="form-label" for="reg-eik">ЕИК / Булстат</label>\
                        <input class="form-input" id="reg-eik" type="text"\
                               placeholder="123456789" required pattern="[0-9]{9,13}">\
                    </div>\
                    <div class="section-title">Вашите данни</div>\
                    <div class="form-group">\
                        <label class="form-label" for="reg-name">Вашето име</label>\
                        <input class="form-input" id="reg-name" type="text"\
                               placeholder="Иван Иванов" required>\
                    </div>\
                    <div class="form-group">\
                        <label class="form-label" for="reg-email">Имейл</label>\
                        <input class="form-input" id="reg-email" type="email"\
                               placeholder="ime@firma.bg" required autocomplete="email">\
                    </div>\
                    <div class="form-group">\
                        <label class="form-label" for="reg-password">Парола</label>\
                        <input class="form-input" id="reg-password" type="password"\
                               placeholder="Минимум 8 символа" required minlength="8"\
                               autocomplete="new-password">\
                    </div>\
                    <div class="section-title">Счетоводител (по желание)</div>\
                    <div class="form-group">\
                        <label class="form-label" for="reg-acc-name">Име на счетоводителя</label>\
                        <input class="form-input" id="reg-acc-name" type="text"\
                               placeholder="Мария Петрова">\
                    </div>\
                    <div class="form-group">\
                        <label class="form-label" for="reg-acc-email">Имейл на счетоводителя</label>\
                        <input class="form-input" id="reg-acc-email" type="email"\
                               placeholder="schetovoditel@abv.bg">\
                    </div>\
                    <button type="submit" class="btn btn-primary btn-block btn-lg mt-16">Регистрация</button>\
                </form>\
                <div class="auth-footer">\
                    Вече имате акаунт? <a href="#/login">Вход</a>\
                </div>\
            </div>\
        </div>';

        var form = document.getElementById('register-form');
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            var errorEl = document.getElementById('reg-error');
            var btn = form.querySelector('button[type="submit"]');

            var data = {
                business_name: document.getElementById('reg-biz-name').value.trim(),
                eik_bulstat: document.getElementById('reg-eik').value.trim(),
                user_name: document.getElementById('reg-name').value.trim(),
                email: document.getElementById('reg-email').value.trim(),
                password: document.getElementById('reg-password').value
            };

            errorEl.classList.add('hidden');
            btn.disabled = true;
            btn.textContent = 'Регистрация...';

            API.register(data)
                .then(function() {
                    // Auto-login after registration
                    return API.login(data.email, data.password);
                })
                .then(function() {
                    window.location.hash = '#/';
                })
                .catch(function(err) {
                    errorEl.textContent = err.message || 'Грешка при регистрация';
                    errorEl.classList.remove('hidden');
                    btn.disabled = false;
                    btn.textContent = 'Регистрация';
                });
        });
    }

    return { render: render };
})();
