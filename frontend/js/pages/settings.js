/**
 * Settings page — business info, accountant, invite, logout.
 */
var SettingsPage = (function() {

    function render(container) {
        var user = API.getUser();
        var isAdmin = user && user.role === 'admin';

        container.innerHTML = '\
        <div class="page">\
            <div class="page-header">\
                <div class="page-title">Настройки</div>\
            </div>\
            <div id="settings-message"></div>\
            <div id="settings-content">\
                <div class="spinner-overlay"><div class="spinner"></div></div>\
            </div>\
        </div>';

        if (isAdmin) {
            loadBusinessData();
        } else {
            showEmployeeView(user);
        }
    }

    function showEmployeeView(user) {
        var contentEl = document.getElementById('settings-content');
        contentEl.innerHTML = '\
        <div class="card">\
            <h3>Профил</h3>\
            <div class="field-row">\
                <div class="field-label">Име</div>\
                <div class="field-value">' + escapeHtml(user.name || '') + '</div>\
            </div>\
            <div class="field-row">\
                <div class="field-label">Имейл</div>\
                <div class="field-value">' + escapeHtml(user.email || '') + '</div>\
            </div>\
            <div class="field-row">\
                <div class="field-label">Роля</div>\
                <div class="field-value">' + escapeHtml(user.role || 'employee') + '</div>\
            </div>\
        </div>\
        <button class="btn btn-danger btn-block mt-16" id="settings-logout">\
            Изход</button>';

        document.getElementById('settings-logout').addEventListener('click', function() {
            API.logout();
        });
    }

    function loadBusinessData() {
        API.getBusiness()
            .then(function(biz) {
                showAdminView(biz);
            })
            .catch(function(err) {
                document.getElementById('settings-content').innerHTML =
                    '<div class="alert alert-danger">' + escapeHtml(err.message) + '</div>\
                     <button class="btn btn-danger btn-block mt-16" id="settings-logout">Изход</button>';
                document.getElementById('settings-logout').addEventListener('click', function() {
                    API.logout();
                });
            });
    }

    function showAdminView(biz) {
        var contentEl = document.getElementById('settings-content');
        contentEl.innerHTML = '\
        <div class="card">\
            <h3>Данни за фирмата</h3>\
            <form id="biz-form">\
                <div class="form-group">\
                    <label class="form-label">Име на фирмата</label>\
                    <input class="form-input" name="name" type="text"\
                           value="' + escapeHtml(biz.name || '') + '">\
                </div>\
                <div class="form-group">\
                    <label class="form-label">ЕИК / Булстат</label>\
                    <input class="form-input" name="eik_bulstat" type="text"\
                           value="' + escapeHtml(biz.eik_bulstat || '') + '">\
                </div>\
                <div class="section-title">Счетоводител</div>\
                <div class="form-group">\
                    <label class="form-label">Име</label>\
                    <input class="form-input" name="accountant_name" type="text"\
                           value="' + escapeHtml(biz.accountant_name || '') + '">\
                </div>\
                <div class="form-group">\
                    <label class="form-label">Имейл</label>\
                    <input class="form-input" name="accountant_email" type="email"\
                           value="' + escapeHtml(biz.accountant_email || '') + '">\
                </div>\
                <button type="submit" class="btn btn-primary btn-block">Запази</button>\
            </form>\
        </div>\
        <div class="card mt-8">\
            <h3>Покани служител</h3>\
            <div id="invite-message"></div>\
            <form id="invite-form">\
                <div class="form-group">\
                    <input class="form-input" id="invite-name" type="text"\
                           placeholder="Име на служителя" required>\
                </div>\
                <div class="form-group">\
                    <input class="form-input" id="invite-email" type="email"\
                           placeholder="Имейл на служителя" required>\
                </div>\
                <div class="form-group">\
                    <input class="form-input" id="invite-password" type="text"\
                           placeholder="Временна парола" required>\
                </div>\
                <button type="submit" class="btn btn-primary btn-block">Покани</button>\
            </form>\
        </div>\
        <button class="btn btn-danger btn-block mt-16" id="settings-logout">Изход</button>';

        // Save business
        document.getElementById('biz-form').addEventListener('submit', function(e) {
            e.preventDefault();
            var form = e.target;
            var btn = form.querySelector('button[type="submit"]');
            var formData = new FormData(form);
            var data = {};
            formData.forEach(function(val, key) { data[key] = val; });

            btn.disabled = true;
            btn.textContent = 'Запазване...';

            API.updateBusiness(data)
                .then(function() {
                    var msgEl = document.getElementById('settings-message');
                    msgEl.innerHTML = '<div class="alert alert-success">Данните са запазени.</div>';
                    btn.disabled = false;
                    btn.textContent = 'Запази';
                    setTimeout(function() { msgEl.innerHTML = ''; }, 3000);
                })
                .catch(function(err) {
                    btn.disabled = false;
                    btn.textContent = 'Запази';
                    alert(err.message || 'Грешка');
                });
        });

        // Invite
        document.getElementById('invite-form').addEventListener('submit', function(e) {
            e.preventDefault();
            var email = document.getElementById('invite-email').value.trim();
            var invMsg = document.getElementById('invite-message');
            if (!email) return;

            var invName = document.getElementById('invite-name').value.trim();
            var invPw = document.getElementById('invite-password').value.trim();
            if (!invName || !invPw) return;

            API.inviteUser({ email: email, name: invName, temp_password: invPw })
                .then(function() {
                    invMsg.innerHTML = '<div class="alert alert-success">Поканата е изпратена до ' +
                        escapeHtml(email) + '</div>';
                    document.getElementById('invite-email').value = '';
                    setTimeout(function() { invMsg.innerHTML = ''; }, 3000);
                })
                .catch(function(err) {
                    invMsg.innerHTML = '<div class="alert alert-danger">' +
                        escapeHtml(err.message) + '</div>';
                });
        });

        // Logout
        document.getElementById('settings-logout').addEventListener('click', function() {
            API.logout();
        });
    }

    return { render: render };
})();
