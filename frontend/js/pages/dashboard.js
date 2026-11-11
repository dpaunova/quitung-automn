/**
 * Dashboard page — month summary, quick scan button, recent receipts.
 */
var DashboardPage = (function() {

    var BG_MONTHS = [
        '', 'Януари', 'Февруари', 'Март', 'Април', 'Май', 'Юни',
        'Юли', 'Август', 'Септември', 'Октомври', 'Ноември', 'Декември'
    ];

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

    function statusIcon(status, hasLowConfidence) {
        if (status === 'failed') return '<span style="color:var(--danger)">✖</span>';
        if (hasLowConfidence) return '<span style="color:var(--warning)">⚠</span>';
        return '<span style="color:var(--success)">✔</span>';
    }

    function render(container) {
        var now = new Date();
        var currentMonth = now.getMonth() + 1;
        var currentYear = now.getFullYear();
        var daysLeft = new Date(currentYear, currentMonth, 0).getDate() - now.getDate();

        container.innerHTML = '\
        <div class="page">\
            <div class="page-header">\
                <div class="page-title">Начало</div>\
                <div class="page-subtitle">' + BG_MONTHS[currentMonth] + ' ' + currentYear + '</div>\
            </div>\
            <div id="dash-reminder" class="alert alert-warning hidden">\
                Остават ' + daysLeft + ' дни до края на месеца. Не забравяйте да изпратите справката!\
            </div>\
            <div class="card">\
                <div class="stats-grid" id="dash-stats">\
                    <div class="stat-item">\
                        <div class="stat-value" id="stat-count">-</div>\
                        <div class="stat-label">Бележки</div>\
                    </div>\
                    <div class="stat-item">\
                        <div class="stat-value" id="stat-total">-</div>\
                        <div class="stat-label">Сума</div>\
                    </div>\
                    <div class="stat-item">\
                        <div class="stat-value" id="stat-vat">-</div>\
                        <div class="stat-label">ДДС</div>\
                    </div>\
                </div>\
            </div>\
            <a href="#/scan" class="btn btn-primary btn-block btn-lg mt-16" style="text-decoration:none">\
                📷 Сканирай бележка\
            </a>\
            <div class="section-title mt-24">Последни бележки</div>\
            <div class="card" id="dash-recent">\
                <div class="spinner-overlay"><div class="spinner"></div></div>\
            </div>\
        </div>';

        // Show reminder if fewer than 5 days left
        if (daysLeft <= 5) {
            document.getElementById('dash-reminder').classList.remove('hidden');
        }

        // Load data
        var mk = currentYear + '-' + String(currentMonth).padStart(2, '0');
        API.getReceipts({ month: mk })
            .then(function(data) {
                var receipts = data.receipts || data || [];
                var count = receipts.length;
                var total = 0;
                var vat = 0;
                receipts.forEach(function(r) {
                    total += parseFloat(r.total_amount || 0);
                    vat += parseFloat(r.vat_amount || 0);
                });

                document.getElementById('stat-count').textContent = count;
                document.getElementById('stat-total').textContent = formatAmount(total);
                document.getElementById('stat-vat').textContent = formatAmount(vat);

                // Last 5 receipts
                var recent = receipts.slice(0, 5);
                var recentEl = document.getElementById('dash-recent');

                if (recent.length === 0) {
                    recentEl.innerHTML = '\
                        <div class="empty-state">\
                            <span class="empty-icon">📄</span>\
                            Няма бележки за този месец\
                        </div>';
                    return;
                }

                var html = '';
                recent.forEach(function(r) {
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
                recentEl.innerHTML = html;
            })
            .catch(function(err) {
                document.getElementById('dash-recent').innerHTML =
                    '<div class="alert alert-danger">' + escapeHtml(err.message) + '</div>';
            });
    }

    return { render: render };
})();
