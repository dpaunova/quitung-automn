/**
 * Scan page — capture receipt image, upload, poll for OCR, show/edit results.
 */
var ScanPage = (function() {

    var pollTimer = null;

    function cleanup() {
        if (pollTimer) {
            clearInterval(pollTimer);
            pollTimer = null;
        }
    }

    function formatAmount(val) {
        if (val === null || val === undefined) return '';
        var num = parseFloat(val);
        if (isNaN(num)) return '';
        var parts = num.toFixed(2).split('.');
        var intPart = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
        return intPart + ',' + parts[1];
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

    function render(container) {
        container.innerHTML = '\
        <div class="page">\
            <div class="page-header">\
                <div class="page-title">Сканирай бележка</div>\
            </div>\
            <div id="scan-upload">\
                <label class="upload-area" for="scan-file">\
                    <span class="upload-icon">📷</span>\
                    <span class="upload-text">Снимайте или изберете касова бележка</span>\
                </label>\
                <input type="file" id="scan-file" accept="image/*" capture="environment"\
                       style="position:absolute;left:-9999px">\
                <div id="scan-preview-area" class="hidden mt-16">\
                    <div class="image-container">\
                        <img id="scan-preview-img" class="image-preview" alt="Преглед">\
                    </div>\
                    <button id="scan-upload-btn" class="btn btn-primary btn-block btn-lg">\
                        ⬆ Качи и обработи\
                    </button>\
                </div>\
            </div>\
            <div id="scan-processing" class="hidden">\
                <div class="spinner-overlay">\
                    <div class="spinner"></div>\
                    <div class="spinner-text">Обработва се...</div>\
                </div>\
            </div>\
            <div id="scan-result" class="hidden"></div>\
            <div id="scan-error" class="hidden"></div>\
        </div>';

        var fileInput = document.getElementById('scan-file');
        var previewArea = document.getElementById('scan-preview-area');
        var previewImg = document.getElementById('scan-preview-img');
        var uploadBtn = document.getElementById('scan-upload-btn');
        var uploadSection = document.getElementById('scan-upload');
        var processingSection = document.getElementById('scan-processing');
        var resultSection = document.getElementById('scan-result');
        var errorSection = document.getElementById('scan-error');

        var selectedFile = null;

        fileInput.addEventListener('change', function(e) {
            var file = e.target.files[0];
            if (!file) return;
            selectedFile = file;
            var reader = new FileReader();
            reader.onload = function(ev) {
                previewImg.src = ev.target.result;
                previewArea.classList.remove('hidden');
            };
            reader.readAsDataURL(file);
        });

        uploadBtn.addEventListener('click', function() {
            if (!selectedFile) return;
            uploadSection.classList.add('hidden');
            processingSection.classList.remove('hidden');

            API.uploadReceipt(selectedFile)
                .then(function(data) {
                    var receiptId = data.id;
                    if (data.status === 'done') {
                        processingSection.classList.add('hidden');
                        API.getReceipt(receiptId).then(function(receipt) {
                            showResult(receipt, resultSection);
                        });
                    } else {
                        pollForResult(receiptId, processingSection, resultSection, errorSection);
                    }
                })
                .catch(function(err) {
                    processingSection.classList.add('hidden');
                    errorSection.innerHTML = '<div class="alert alert-danger">' +
                        escapeHtml(err.message) + '</div>\
                        <button class="btn btn-secondary btn-block mt-8" onclick="window.location.hash=\'#/scan\'">\
                        Опитай отново</button>';
                    errorSection.classList.remove('hidden');
                });
        });
    }

    function pollForResult(receiptId, processingEl, resultEl, errorEl) {
        pollTimer = setInterval(function() {
            API.getReceipt(receiptId)
                .then(function(receipt) {
                    if (receipt.status === 'done') {
                        cleanup();
                        processingEl.classList.add('hidden');
                        showResult(receipt, resultEl);
                    } else if (receipt.status === 'failed') {
                        cleanup();
                        processingEl.classList.add('hidden');
                        errorEl.innerHTML = '<div class="alert alert-danger">\
                            Обработката не успя. Моля, опитайте отново.</div>\
                            <button class="btn btn-secondary btn-block mt-8" onclick="window.location.hash=\'#/scan\'">\
                            Опитай отново</button>';
                        errorEl.classList.remove('hidden');
                    }
                })
                .catch(function() {});
        }, 2000);
    }

    function showResult(receipt, resultEl) {
        var conf = receipt.field_confidence || {};
        var fields = [
            { key: 'supplier_name', dbKey: 'supplier_name', label: 'Доставчик', type: 'text' },
            { key: 'receipt_date', dbKey: 'receipt_date', label: 'Дата', type: 'text' },
            { key: 'receipt_number', dbKey: 'receipt_number', label: 'Номер на бележка', type: 'text' },
            { key: 'total_amount', dbKey: 'total_amount', label: 'Обща сума (лв.)', type: 'number' },
            { key: 'vat_amount', dbKey: 'vat_amount', label: 'ДДС (лв.)', type: 'number' }
        ];

        var html = '<div class="card"><h3>Резултат от сканиране</h3>';
        html += '<div class="alert alert-info mb-16">Проверете и коригирайте данните при нужда. Жълто маркираните полета имат ниска сигурност.</div>';
        html += '<form id="scan-result-form">';

        fields.forEach(function(f) {
            var fieldConf = conf[f.key] !== undefined ? conf[f.key] : (conf[f.dbKey] !== undefined ? conf[f.dbKey] : null);
            var cls = confidenceClass(fieldConf);
            var val = receipt[f.dbKey] || '';
            if (f.type === 'number' && val) val = formatAmount(val);
            if (f.key === 'receipt_date' && val) {
                var d = new Date(val);
                if (!isNaN(d.getTime())) {
                    val = String(d.getDate()).padStart(2, '0') + '.' +
                          String(d.getMonth() + 1).padStart(2, '0') + '.' +
                          d.getFullYear();
                }
            }

            html += '<div class="field-row ' + cls + '">';
            html += '<div class="field-label">' + f.label + ' ' + confidenceDot(fieldConf) + '</div>';
            html += '<input class="form-input" name="' + f.dbKey + '" type="text" value="' + escapeHtml(String(val)) + '">';
            html += '</div>';
        });

        html += '<button type="submit" class="btn btn-success btn-block btn-lg mt-16">\
                 ✔ Запази</button>';
        html += '</form></div>';

        html += '<a href="#/scan" class="btn btn-secondary btn-block mt-8" style="text-decoration:none">\
                 Сканирай нова бележка</a>';

        resultEl.innerHTML = html;
        resultEl.classList.remove('hidden');

        var form = document.getElementById('scan-result-form');
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

            API.updateReceipt(receipt.id, updates)
                .then(function() {
                    btn.textContent = 'Запазено!';
                    btn.style.backgroundColor = 'var(--success)';
                    setTimeout(function() {
                        window.location.hash = '#/receipts/' + receipt.id;
                    }, 800);
                })
                .catch(function(err) {
                    btn.disabled = false;
                    btn.textContent = '✔ Запази';
                    alert(err.message || 'Грешка при запазване');
                });
        });
    }

    return { render: render, cleanup: cleanup };
})();
