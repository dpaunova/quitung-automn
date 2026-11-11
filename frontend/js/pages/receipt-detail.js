/**
 * Receipt detail page — view photo, edit fields, save/delete.
 */
var ReceiptDetailPage = (function() {

    function formatAmount(val) {
        if (val === null || val === undefined) return '';
        var num = parseFloat(val);
        if (isNaN(num)) return '';
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

    function confidenceClass(confidence) {
        if (confidence === undefined || confidence === null) return '';
        return confidence >= 0.85 ? 'confidence-high' : 'confidence-low';
    }

    function confidenceDot(confidence) {
        if (confidence === undefined || confidence === null) return '';
        var cls = confidence >= 0.85 ? 'high' : 'low';
        var pct = Math.round(confidence * 100);
        return '<span class="confidence-dot ' + cls + '"></span>' + pct + '%';
    }

    function render(container, params) {
        var receiptId = params.id;

        container.innerHTML = '\
        <div class="page">\
            <div class="page-header flex justify-between items-center">\
                <div class="page-title">Бележка</div>\
                <a href="#/receipts" style="color:var(--primary);text-decoration:none;font-size:0.9rem">← Назад</a>\
            </div>\
            <div id="detail-content">\
                <div class="spinner-overlay"><div class="spinner"></div></div>\
            </div>\
        </div>';

        API.getReceipt(receiptId)
            .then(function(receipt) {
                showDetail(receipt, receiptId);
            })
            .catch(function(err) {
                document.getElementById('detail-content').innerHTML =
                    '<div class="alert alert-danger">' + escapeHtml(err.message) + '</div>';
            });
    }

    function showDetail(receipt, receiptId) {
        var contentEl = document.getElementById('detail-content');
        var user = API.getUser();
        var isAdmin = user && user.role === 'admin';
        var conf = receipt.field_confidence || {};

        var fields = [
            { key: 'supplier_name', label: 'Доставчик', type: 'text' },
            { key: 'receipt_date', label: 'Дата', type: 'text' },
            { key: 'receipt_number', label: 'Номер на бележка', type: 'text' },
            { key: 'total_amount', label: 'Обща сума (лв.)', type: 'number' },
            { key: 'vat_amount', label: 'ДДС (лв.)', type: 'number' }
        ];

        var html = '';

        if (receipt.photo_url) {
            html += '<div class="image-container mb-16">\
                <img class="image-zoomable" id="detail-img" src="' + escapeHtml(receipt.photo_url) + '"\
                     alt="Снимка на бележка">\
            </div>';
        }

        html += '<div class="card">';
        html += '<form id="detail-form">';

        fields.forEach(function(f) {
            var fieldConf = conf[f.key] !== undefined ? conf[f.key] : null;
            var cls = confidenceClass(fieldConf);
            var val = receipt[f.key] || '';
            if (f.type === 'number' && val) val = formatAmount(val);
            if (f.key === 'receipt_date' && val) {
                val = formatDate(val);
            }

            html += '<div class="field-row ' + cls + '">';
            html += '<div class="field-label">' + f.label + ' ' + confidenceDot(fieldConf) + '</div>';
            html += '<input class="form-input" name="' + f.key + '" type="text" value="' + escapeHtml(String(val)) + '">';
            html += '</div>';
        });

        html += '<button type="submit" class="btn btn-success btn-block mt-16">\
                 ✔ Запази корекции</button>';
        html += '</form>';

        if (isAdmin) {
            html += '<button id="detail-delete-btn" class="btn btn-danger btn-block mt-8">\
                     ✖ Изтрий</button>';
        }

        html += '</div>';

        html += '<div class="card mt-8">';
        html += '<div class="field-label">Статус</div>';
        var statusText = receipt.status === 'done' ? 'Обработена'
            : receipt.status === 'failed' ? 'Грешка' : 'В обработка';
        html += '<div class="field-value">' + statusText + '</div>';
        if (receipt.is_corrected) {
            html += '<div class="badge badge-success mt-4">Коригирана</div>';
        }
        html += '</div>';

        contentEl.innerHTML = html;

        var img = document.getElementById('detail-img');
        if (img) {
            img.addEventListener('click', function() {
                img.classList.toggle('zoomed');
            });
        }

        var form = document.getElementById('detail-form');
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            var formData = new FormData(form);
            var updates = {};
            formData.forEach(function(val, key) {
                if (key === 'total_amount' || key === 'vat_amount') {
                    val = val.replace(/\s/g, '').replace(',', '.');
                    updates[key] = parseFloat(val) || null;
                } else if (key === 'receipt_date') {
                    var parts = val.split('.');
                    if (parts.length === 3) {
                        updates[key] = parts[2] + '-' + parts[1] + '-' + parts[0] + 'T00:00:00';
                    } else {
                        updates[key] = val;
                    }
                } else {
                    updates[key] = val;
                }
            });

            var btn = form.querySelector('button[type="submit"]');
            btn.disabled = true;
            btn.textContent = 'Запазване...';

            API.updateReceipt(receiptId, updates)
                .then(function() {
                    btn.textContent = 'Запазено!';
                    btn.style.backgroundColor = 'var(--success)';
                    setTimeout(function() {
                        btn.textContent = '✔ Запази корекции';
                        btn.style.backgroundColor = '';
                        btn.disabled = false;
                    }, 1500);
                })
                .catch(function(err) {
                    btn.disabled = false;
                    btn.textContent = '✔ Запази корекции';
                    alert(err.message || 'Грешка при запазване');
                });
        });

        var deleteBtn = document.getElementById('detail-delete-btn');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', function() {
                showDeleteDialog(receiptId);
            });
        }
    }

    function showDeleteDialog(receiptId) {
        var overlay = document.createElement('div');
        overlay.className = 'dialog-overlay';
        overlay.innerHTML = '\
            <div class="dialog">\
                <div class="dialog-title">Изтриване на бележка</div>\
                <div class="dialog-text">Сигурни ли сте, че искате да изтриете тази бележка? Това действие е необратимо.</div>\
                <div class="dialog-actions">\
                    <button class="btn btn-secondary" id="dialog-cancel">Отказ</button>\
                    <button class="btn btn-danger" id="dialog-confirm">Изтрий</button>\
                </div>\
            </div>';

        document.body.appendChild(overlay);

        document.getElementById('dialog-cancel').addEventListener('click', function() {
            overlay.remove();
        });

        overlay.addEventListener('click', function(e) {
            if (e.target === overlay) overlay.remove();
        });

        document.getElementById('dialog-confirm').addEventListener('click', function() {
            API.deleteReceipt(receiptId)
                .then(function() {
                    overlay.remove();
                    window.location.hash = '#/receipts';
                })
                .catch(function(err) {
                    alert(err.message || 'Грешка при изтриване');
                    overlay.remove();
                });
        });
    }

    return { render: render };
})();
