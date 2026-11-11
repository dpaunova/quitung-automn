/**
 * App initialization — registers routes, renders bottom nav, boots the router.
 */
(function() {

    // ---- Utility: HTML escaping (global) ----
    window.escapeHtml = function(str) {
        if (!str) return '';
        var div = document.createElement('div');
        div.appendChild(document.createTextNode(str));
        return div.innerHTML;
    };

    // ---- Register routes ----
    Router.register('/login', function(el) { LoginPage.render(el); });
    Router.register('/register', function(el) { RegisterPage.render(el); });
    Router.register('/', function(el) { renderWithNav(el, DashboardPage); });
    Router.register('/scan', function(el) { renderWithNav(el, ScanPage); });
    Router.register('/receipts', function(el) { renderWithNav(el, ReceiptsPage); });
    Router.register('/receipts/:id', function(el, params) { renderWithNav(el, ReceiptDetailPage, params); });
    Router.register('/report', function(el) { renderWithNav(el, ReportPage); });
    Router.register('/settings', function(el) { renderWithNav(el, SettingsPage); });

    /**
     * Render a page wrapped with the bottom navigation.
     */
    function renderWithNav(container, page, params) {
        // Cleanup previous page poll timers etc.
        if (typeof ScanPage !== 'undefined' && ScanPage.cleanup) {
            ScanPage.cleanup();
        }

        // Create page content area + nav
        var wrapper = document.createElement('div');
        var content = document.createElement('div');
        content.id = 'page-content';
        wrapper.appendChild(content);
        wrapper.appendChild(createNav());
        container.appendChild(wrapper);

        // Render the page
        page.render(content, params || {});
    }

    /**
     * Build the bottom navigation bar.
     */
    function createNav() {
        var nav = document.createElement('nav');
        nav.className = 'bottom-nav';

        var items = [
            { route: '/',         icon: '⌂',   label: 'Начало' },
            { route: '/scan',     icon: '📷', label: 'Сканирай', scan: true },
            { route: '/receipts', icon: '📄', label: 'Бележки' },
            { route: '/report',   icon: '📊', label: 'Справка' },
            { route: '/settings', icon: '⚙',   label: 'Настройки' }
        ];

        var currentPath = (window.location.hash.replace(/^#/, '') || '/').split('?')[0];

        items.forEach(function(item) {
            var btn = document.createElement('button');
            btn.className = 'nav-item';
            if (item.scan) btn.className += ' nav-scan';
            btn.setAttribute('data-route', item.route);

            if (currentPath === item.route ||
                (item.route !== '/' && currentPath.indexOf(item.route) === 0)) {
                btn.classList.add('active');
            }

            btn.innerHTML = '<span class="nav-icon">' + item.icon + '</span>' +
                            '<span class="nav-label">' + item.label + '</span>';

            btn.addEventListener('click', function() {
                window.location.hash = '#' + item.route;
            });

            nav.appendChild(btn);
        });

        return nav;
    }

    // ---- Boot ----
    Router.init();

})();
