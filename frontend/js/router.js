/**
 * Simple hash-based SPA router.
 * Routes: #/login, #/register, #/, #/scan, #/receipts, #/receipts/:id,
 *         #/report, #/settings
 * Auth guard: redirects to #/login if no token (except login/register pages).
 */
var Router = (function() {
    var routes = {};
    var currentPage = null;

    function register(path, handler) {
        routes[path] = handler;
    }

    /**
     * Match the current hash against registered routes.
     * Supports :id parameters.
     */
    function matchRoute(hash) {
        // Normalize: remove leading #, default to /
        var path = hash.replace(/^#/, '') || '/';

        // Exact match first
        if (routes[path]) {
            return { handler: routes[path], params: {} };
        }

        // Parameter matching (e.g. /receipts/:id)
        var routeKeys = Object.keys(routes);
        for (var i = 0; i < routeKeys.length; i++) {
            var routePath = routeKeys[i];
            var routeParts = routePath.split('/');
            var pathParts = path.split('/');

            if (routeParts.length !== pathParts.length) continue;

            var params = {};
            var matched = true;
            for (var j = 0; j < routeParts.length; j++) {
                if (routeParts[j].charAt(0) === ':') {
                    params[routeParts[j].substring(1)] = pathParts[j];
                } else if (routeParts[j] !== pathParts[j]) {
                    matched = false;
                    break;
                }
            }

            if (matched) {
                return { handler: routes[routePath], params: params };
            }
        }

        return null;
    }

    /**
     * Navigate to a route. Called on hashchange and manually.
     */
    function navigate() {
        var hash = window.location.hash;
        var path = hash.replace(/^#/, '') || '/';

        // Auth guard: public pages are login and register only
        var publicPages = ['/login', '/register'];
        if (!API.isLoggedIn() && publicPages.indexOf(path) === -1) {
            window.location.hash = '#/login';
            return;
        }

        // If logged in and on login/register, redirect to dashboard
        if (API.isLoggedIn() && (path === '/login' || path === '/register')) {
            window.location.hash = '#/';
            return;
        }

        var match = matchRoute(hash);
        if (match) {
            var app = document.getElementById('app');
            app.innerHTML = '';
            currentPage = path;
            match.handler(app, match.params);
            updateNav(path);
        } else {
            // 404: go to dashboard or login
            window.location.hash = API.isLoggedIn() ? '#/' : '#/login';
        }
    }

    function updateNav(path) {
        var navItems = document.querySelectorAll('.nav-item');
        navItems.forEach(function(item) {
            var href = item.getAttribute('data-route');
            if (!href) return;
            if (path === href || (href !== '/' && path.indexOf(href) === 0)) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
    }

    function getCurrentPage() {
        return currentPage;
    }

    function init() {
        window.addEventListener('hashchange', navigate);
        navigate();
    }

    return {
        register: register,
        navigate: navigate,
        init: init,
        getCurrentPage: getCurrentPage
    };
})();
