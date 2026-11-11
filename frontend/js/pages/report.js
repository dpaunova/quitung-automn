/**
 * Report page — preview monthly report, send to accountant, view history.
 */
var ReportPage = (function() {

    var BG_MONTHS = [
        '', 'Януари', 'Февруари', 'Март', 'Април', 'Май', 'Юни',
        'Юли', 'Август', 'Септември', 'Октомври', 'Ноември', 'Декември'
    ];

    var currentYear, currentMonth;

    function formatAmount(val) {
        if (val === null || val === undefined) return '0,00';
        var num = parseFloat(val);
        if (isNaN(num)) return '0,00';
        var parts = num.toFixed(2).split('.');
        var intPart = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
        return intPart + ',' + parts[1];
    }

    function formatDate(dateStr) {
        if (!dateStr) return '';
        var d = new Date(dateStr);
        var dd = String(d.getDate()).padStart(2, '0');
        var mm = String(d.getMonth() + 1).padStart(2, '0');
        var yyyy = d.getFullYear();
        return dd + '.' + mm + '.' + yyyy;
    }

    function monthKey() {
        return currentYear + '-' + String(currentMonth).padStart(2, '0');
    }

    function changeMonth(delta) {
        currentMonth += delta;
        if (currentMonth > 12) { currentMonth = 1; currentYear++; }
        if (currentMonth < 1) { currentMonth = 12; currentYear--; }
        updateLabel();
        loadPreview();
    }

    function updateLabel() {
        var el = document.getElementById('report-month-label');
        if (el) el.textContent = BG_MONTHS[currentMonth] + ' ' + currentYear;
    }

    function loadPreview() {
        var previewEl = document.getElementById('report-preview');
        var sendBtn = document.getElementById('report-send-btn');
        if (!previewEl) return;

        previewEl.innerHTML = '<div class="spinner-overlay"><div class="spinner"></div></div>';
        if (sendBtn) sendBtn.classList.add('hidden');

        var mk = monthKey();

        API.getReceipts({ month: mk })
            .then(function(receipts) {
                if (!receipts || receipts.length === 0) {
                    previewEl.innerHTML = '<div class="empty-state">\
                        <span class="empty-icon">📊</span>\
                        Няма бележки за този месец</div>';
                    return;
                }

                var html = '<div class="table-wrapper"><table>';
                html += '<thead><tr>\
                    <th>№</th>\
                    <th>Дата</th>\
                    <th>Доставчик</th>\
                    <th>Бел. №</th>\
                    <th>Сума</th>\
                    <th>ДДС</th>\
                </tr></thead>';
                html += '<tbody>';

                var totalAll = 0, totalVat = 0;

                receipts.forEach(function(r, i) {
                    var total = parseFloat(r.total_amount || 0);
                    var vat = parseFloat(r.vat_amount || 0);
                    totalAll += total;
                    totalVat += vat;

                    var hasLow = false;
                    if (r.field_confidence) {
                        Object.keys(r.field_confidence).forEach(function(k) {
                            if (r.field_confidence[k] < 0.85) hasLow = true;
                        });
                    }
                    var rowClass = hasLow ? 'row-warning' : '';
                    html += '<tr class="' + rowClass + '">';
                    html += '<td>' + (i + 1) + '</td>';
                    html += '<td>' + formatDate(r.receipt_date) + '</td>';
                    html += '<td>' + escapeHtml(r.supplier_name || '') + '</td>';
                    html += '<td>' + escapeHtml(r.receipt_number || '') + '</td>';
                    html += '<td>' + formatAmount(r.total_amount) + ' лв.</td>';
                    html += '<td>' + formatAmount(r.vat_amount) + ' лв.</td>';
                    html += '</tr>';
                });

                html += '<tr class="row-total">';
                html += '<td colspan="4">Общо</td>';
                html += '<td>' + formatAmount(totalAll) + ' лв.</td>';
                html += '<td>' + formatAmount(totalVat) + ' лв.</td>';
                html += '</tr>';

                html += '</tbody></table></div>';

                previewEl.innerHTML = html;
                if (sendBtn) sendBtn.classList.remove('hidden');
            })
            .catch(function(err) {
                previewEl.innerHTML = '<div class="alert alert-danger">' + escapeHtml(err.message) + '</div>';
            });
    }

    function loadHistory() {
        var historyEl = document.getElementById('report-history');
        if (!historyEl) return;

        API.getReports()
            .then(function(reports) {
                if (!reports || reports.length === 0) {
                    historyEl.innerHTML = '<div class="empty-state" style="padding:16px">\
                        Няма изпратени справки</div>';
                    return;
                }

                var html = '';
                reports.forEach(function(r) {
                    var parts = r.month ? r.month.split('-') : [];
                    var y = parts[0] || '';
                    var m = parseInt(parts[1] || '0');
                    var label = (BG_MONTHS[m] || '') + ' ' + y;

                    html += '<div class="receipt-item">';
                    html += '<div class="receipt-status"><span style="color:var(--success)">✔</span></div>';
                    html += '<div class="receipt-info">';
                    html += '<div class="receipt-supplier">' + escapeHtml(label) + '</div>';
                    html += '<div class="receipt-date">Изпратена на ' + formatDate(r.sent_at) + '</div>';
                    html += '</div>';
                    html += '<div class="badge badge-success">Изпратена</div>';
                    html += '</div>';
                });
                historyEl.innerHTML = html;
            })
            .catch(function() {
                historyEl.innerHTML = '';
            });
    }

    function showSendDialog() {
        var mk = monthKey();
        var overlay = document.createElement('div');
        overlay.className = 'dialog-overlay';
        overlay.innerHTML = '\
            <div class="dialog">\
                <div class="dialog-title">Изпрати справка</div>\
                <div class="dialog-text">Сигурни ли сте, че искате да изпратите справката за ' +
                BG_MONTHS[currentMonth] + ' ' + currentYear + ' на счетоводителя?</div>\
                <div class="dialog-actions">\
                    <button class="btn btn-secondary" id="send-cancel">Отказ</button>\
                    <button class="btn btn-primary" id="send-confirm">Изпрати</button>\
                </div>\
            </div>';

        document.body.appendChild(overlay);

        document.getElementById('send-cancel').addEventListener('click', function() {
            overlay.remove();
        });

        overlay.addEventListener('click', function(e) {
            if (e.target === overlay) overlay.remove();
        });

        document.getElementById('send-confirm').addEventListener('click', function() {
            var confirmBtn = document.getElementById('send-confirm');
            confirmBtn.disabled = true;
            confirmBtn.textContent = 'Изпращане...';

            API.sendReport(mk)
                .then(function() {
                    overlay.remove();
                    var msgEl = document.getElementById('report-message');
                    if (msgEl) {
                        msgEl.innerHTML = '<div class="alert alert-success">\
                            Справката е изпратена успешно!</div>';
                    }
                    loadHistory();
                })
                .catch(function(err) {
                    overlay.remove();
                    var msgEl = document.getElementById('report-message');
                    if (msgEl) {
                        msgEl.innerHTML = '<div class="alert alert-danger">' +
                            escapeHtml(err.message) + '</div>';
                    }
                });
        });
    }

    function render(container) {
        var now = new Date();
        currentYear = now.getFullYear();
        currentMonth = now.getMonth() + 1;

        container.innerHTML = '\
        <div class="page">\
            <div class="page-header">\
                <div class="page-title">Справка</div>\
            </div>\
            <div class="month-selector">\
                <button id="report-prev">❮</button>\
                <span class="month-label" id="report-month-label"></span>\
                <button id="report-next">❯</button>\
            </div>\
            <div id="report-message"></div>\
            <div class="card" id="report-preview">\
                <div class="spinner-overlay"><div class="spinner"></div></div>\
            </div>\
            <button id="report-send-btn" class="btn btn-primary btn-block btn-lg mt-8 hidden">\
                ✉ Изпрати на счетоводителя\
            </button>\
            <div class="section-title mt-24">История на изпратени справки</div>\
            <div class="card" id="report-history">\
                <div class="spinner-overlay"><div class="spinner"></div></div>\
            </div>\
        </div>';

        updateLabel();
        loadPreview();
        loadHistory();

        document.getElementById('report-prev').addEventListener('click', function() { changeMonth(-1); });
        document.getElementById('report-next').addEventListener('click', function() { changeMonth(1); });
        document.getElementById('report-send-btn').addEventListener('click', showSendDialog);
    }

    return { render: render };
})();
