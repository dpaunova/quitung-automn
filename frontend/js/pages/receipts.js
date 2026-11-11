/**
 * Receipts list page — month filter, receipt cards.
 */
var ReceiptsPage = (function() {

    var BG_MONTHS = [
        '', 'Януари', 'Февруари', 'Март', 'Април', 'Май', 'Юни',
        'Юли', 'Август', 'Септември', 'Октомври', 'Ноември', 'Декември'
    ];

    var currentYear, currentMonth;

    function formatAmount(val) {
        if (val === null || val === undefined) return '0,00 лв.';
        var num = parseFloat(val);
        if (isNaN(num)) return '0,00 лв.';
        var parts = num.toFixed(2).split('.');
        var intPart = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
        return intPart + ',' + parts[1] + ' лв.';
    }

    function formatDate(dateStr) {
        if (!dateStr) return '';
        var d = new Date(dateStr);
        var dd = String(d.getDate()).padStart(2, '0');
        var mm = String(d.getMonth() + 1).padStart(2, '0');
        var yyyy = d.getFullYear();
        return dd + '.' + mm + '.' + yyyy;
    }

    function statusIcon(status, hasLow) {
        if (status === 'failed') return '<span style="color:var(--danger)">✖</span>';
        if (hasLow) return '<span style="color:var(--warning)">⚠</span>';
        return '<span style="color:var(--success)">✔</span>';
    }

    function changeMonth(delta) {
        currentMonth += delta;
        if (currentMonth > 12) { currentMonth = 1; currentYear++; }
        if (currentMonth < 1) { currentMonth = 12; currentYear--; }
        updateLabel();
        loadReceipts();
    }

    function updateLabel() {
        var label = document.getElementById('receipts-month-label');
        if (label) {
            label.textContent = BG_MONTHS[currentMonth] + ' ' + currentYear;
        }
    }

    function loadReceipts() {
        var listEl = document.getElementById('receipts-list');
        if (!listEl) return;
        listEl.innerHTML = '<div class="spinner-overlay"><div class="spinner"></div></div>';

        var mk = currentYear + '-' + String(currentMonth).padStart(2, '0');
        API.getReceipts({ month: mk })
            .then(function(data) {
                var receipts = data.receipts || data || [];
                if (receipts.length === 0) {
                    listEl.innerHTML = '<div class="empty-state">\
                        <span class="empty-icon">📄</span>\
                        Няма бележки за този месец</div>';
                    return;
                }

                var html = '';
                receipts.forEach(function(r) {
                    var hasLow = false;
                    if (r.field_confidence) {
                        Object.keys(r.field_confidence).forEach(function(k) {
                            if (r.field_confidence[k] < 0.85) hasLow = true;
                        });
                    }
                    html += '<div class="receipt-item" onclick="window.location.hash=\'#/receipts/' + r.id + '\'">';
                    html += '<div class="receipt-status">' + statusIcon(r.status, hasLow) + '</div>';
                    html += '<div class="receipt-info">';
                    html += '<div class="receipt-supplier">' + escapeHtml(r.supplier_name || 'Неизвестен') + '</div>';
                    html += '<div class="receipt-date">' + formatDate(r.receipt_date) + '</div>';
                    html += '</div>';
                    html += '<div class="receipt-amount">' + formatAmount(r.total_amount) + '</div>';
                    html += '</div>';
                });
                listEl.innerHTML = html;
            })
            .catch(function(err) {
                listEl.innerHTML = '<div class="alert alert-danger">' + escapeHtml(err.message) + '</div>';
            });
    }

    function render(container) {
        var now = new Date();
        currentYear = now.getFullYear();
        currentMonth = now.getMonth() + 1;

        container.innerHTML = '\
        <div class="page">\
            <div class="page-header">\
                <div class="page-title">Бележки</div>\
            </div>\
            <div class="month-selector">\
                <button id="receipts-prev">❮</button>\
                <span class="month-label" id="receipts-month-label"></span>\
                <button id="receipts-next">❯</button>\
            </div>\
            <div class="card" id="receipts-list">\
                <div class="spinner-overlay"><div class="spinner"></div></div>\
            </div>\
        </div>';

        updateLabel();
        loadReceipts();

        document.getElementById('receipts-prev').addEventListener('click', function() { changeMonth(-1); });
        document.getElementById('receipts-next').addEventListener('click', function() { changeMonth(1); });
    }

    return { render: render };
})();
