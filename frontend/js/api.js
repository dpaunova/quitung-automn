/**
 * API Client — handles all backend communication.
 * Stores JWT in localStorage. Adds Authorization header automatically.
 * Redirects to #/login on 401.
 */
var API = (function() {
    var BASE = '/api';

    function getToken() {
        return localStorage.getItem('beleg_token');
    }

    function setToken(token) {
        localStorage.setItem('beleg_token', token);
    }

    function clearToken() {
        localStorage.removeItem('beleg_token');
        localStorage.removeItem('beleg_user');
    }

    function getUser() {
        try {
            var data = localStorage.getItem('beleg_user');
            return data ? JSON.parse(data) : null;
        } catch (e) {
            return null;
        }
    }

    function setUser(user) {
        localStorage.setItem('beleg_user', JSON.stringify(user));
    }

    function isLoggedIn() {
        return !!getToken();
    }

    function request(method, path, body, isFormData) {
        var headers = {};

        if (!isFormData) {
            headers['Content-Type'] = 'application/json';
        }

        var token = getToken();
        if (token) {
            headers['Authorization'] = 'Bearer ' + token;
        }

        var opts = {
            method: method,
            headers: headers
        };

        if (body) {
            opts.body = isFormData ? body : JSON.stringify(body);
        }

        return fetch(BASE + path, opts)
            .then(function(res) {
                if (res.status === 401) {
                    clearToken();
                    window.location.hash = '#/login';
                    return Promise.reject(new Error('Сесията е изтекла. Моля, влезте отново.'));
                }
                if (!res.ok) {
                    return res.json().then(function(data) {
                        return Promise.reject(new Error(data.detail || data.message || 'Грешка от сървъра'));
                    }).catch(function(parseErr) {
                        if (parseErr.message && parseErr.message !== 'Грешка от сървъра') {
                            return Promise.reject(parseErr);
                        }
                        return Promise.reject(new Error('Грешка: ' + res.status));
                    });
                }
                if (res.status === 204) {
                    return null;
                }
                return res.json();
            });
    }

    // ---- Auth ----

    function register(data) {
        return request('POST', '/auth/register', {
            business_name: data.business_name,
            eik_bulstat: data.eik_bulstat,
            vat_number: data.vat_number || null,
            user_name: data.user_name,
            email: data.email,
            password: data.password
        });
    }

    function login(email, password) {
        return request('POST', '/auth/login', { email: email, password: password })
            .then(function(res) {
                if (res.access_token) {
                    setToken(res.access_token);
                    if (res.user) {
                        setUser(res.user);
                    }
                }
                return res;
            });
    }

    function logout() {
        clearToken();
        window.location.hash = '#/login';
    }

    // ---- Receipts ----

    function uploadReceipt(file) {
        var formData = new FormData();
        formData.append('file', file);
        return request('POST', '/receipts/', formData, true);
    }

    function getReceipts(params) {
        var query = '';
        if (params) {
            var parts = [];
            Object.keys(params).forEach(function(key) {
                if (params[key] !== undefined && params[key] !== null) {
                    parts.push(encodeURIComponent(key) + '=' + encodeURIComponent(params[key]));
                }
            });
            if (parts.length) {
                query = '?' + parts.join('&');
            }
        }
        return request('GET', '/receipts/' + query);
    }

    function getReceipt(id) {
        return request('GET', '/receipts/' + id);
    }

    function updateReceipt(id, data) {
        return request('PATCH', '/receipts/' + id, data);
    }

    function deleteReceipt(id) {
        return request('DELETE', '/receipts/' + id);
    }

    // ---- Reports ----

    function getReportPreview(month) {
        return request('GET', '/reports/preview?month=' + encodeURIComponent(month));
    }

    function sendReport(month) {
        return request('POST', '/reports/send', { month: month });
    }

    function getReports() {
        return request('GET', '/reports/');
    }

    // ---- Business ----

    function getBusiness() {
        return request('GET', '/business/');
    }

    function updateBusiness(data) {
        return request('PATCH', '/business/', data);
    }

    function inviteUser(data) {
        return request('POST', '/auth/invite', data);
    }

    // ---- Public API ----

    return {
        getToken: getToken,
        getUser: getUser,
        setUser: setUser,
        isLoggedIn: isLoggedIn,
        register: register,
        login: login,
        logout: logout,
        uploadReceipt: uploadReceipt,
        getReceipts: getReceipts,
        getReceipt: getReceipt,
        updateReceipt: updateReceipt,
        deleteReceipt: deleteReceipt,
        getReportPreview: getReportPreview,
        sendReport: sendReport,
        getReports: getReports,
        getBusiness: getBusiness,
        updateBusiness: updateBusiness,
        inviteUser: inviteUser
    };
})();
