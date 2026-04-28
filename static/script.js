document.addEventListener('DOMContentLoaded', () => {
    // File Drop Areas interactivity
    const setupDropArea = (dropAreaId, inputId) => {
        const dropArea = document.getElementById(dropAreaId);
        const input = document.getElementById(inputId);
        const fileMsg = dropArea.querySelector('.file-msg');

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        ['dragenter', 'dragover'].forEach(eventName => {
            dropArea.addEventListener(eventName, () => dropArea.classList.add('is-active'), false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, () => dropArea.classList.remove('is-active'), false);
        });

        dropArea.addEventListener('drop', (e) => {
            let dt = e.dataTransfer;
            let files = dt.files;
            input.files = files;
            updateFileMsg();
        });

        input.addEventListener('change', updateFileMsg);

        function updateFileMsg() {
            if(input.files.length > 0) {
                fileMsg.textContent = input.files[0].name;
            } else {
                fileMsg.textContent = "or drag and drop here";
            }
        }
    };

    setupDropArea('code-drop', 'code-file');
    setupDropArea('schema-drop', 'schema-file');

    // Form Submission
    const form = document.getElementById('analyze-form');
    const analyzeBtn = document.getElementById('analyze-btn');
    const loader = document.getElementById('loader');
    const resultsContent = document.getElementById('results-content');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const codeFile = document.getElementById('code-file').files[0];
        const schemaFile = document.getElementById('schema-file').files[0];

        if(!codeFile || !schemaFile) {
            alert('Please select both a code file and a schema file.');
            return;
        }

        // UI Loading state
        analyzeBtn.disabled = true;
        loader.classList.remove('hidden');
        analyzeBtn.querySelector('span').textContent = "Analyzing...";
        resultsContent.innerHTML = `<div class="placeholder"><div class="loader" style="margin: 0 auto; width: 40px; height: 40px;"></div></div>`;

        const formData = new FormData();
        formData.append('code_file', codeFile);
        formData.append('schema_file', schemaFile);

        try {
            const response = await fetch('/analyze', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "Server Error");
            }

            const data = await response.json();
            renderDiagnostics(data);
        } catch (error) {
            resultsContent.innerHTML = `
                <div class="diagnostic-item error" style="border-left-color: #ef4444;">
                    <div class="diag-content">
                        <div class="diag-message" style="color: #ef4444;">❌ Failed to analyze: ${error.message}</div>
                    </div>
                </div>
            `;
        } finally {
            analyzeBtn.disabled = false;
            loader.classList.add('hidden');
            analyzeBtn.querySelector('span').textContent = "Analyze Code";
        }
    });

    function renderDiagnostics(data) {
        if(data.diagnostics.length === 0) {
            resultsContent.innerHTML = `
                <div class="summary-card">
                    ${data.summary}
                </div>
                <div class="success-box">
                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                    <h3>Perfect! No issues found.</h3>
                    <p>Your code passed all schema validation rules.</p>
                </div>
            `;
            return;
        }

        // Count diagnostics
        const counts = { error: 0, warning: 0, info: 0 };
        data.diagnostics.forEach(d => {
            counts[d.level.toLowerCase()]++;
        });

        let html = `
            <div class="stats-dashboard">
                <div class="stat-box error">
                    <div class="stat-count">${counts.error}</div>
                    <div class="stat-label">Errors</div>
                </div>
                <div class="stat-box warning">
                    <div class="stat-count">${counts.warning}</div>
                    <div class="stat-label">Warnings</div>
                </div>
                <div class="stat-box info">
                    <div class="stat-count">${counts.info}</div>
                    <div class="stat-label">Infos</div>
                </div>
            </div>
            <div class="summary-card">${data.summary}</div>
        `;
        
        data.diagnostics.forEach((diag, index) => {
            const levelClass = diag.level.toLowerCase();
            const delay = index * 0.1;
            
            html += `
                <div class="diagnostic-item ${levelClass}" style="animation-delay: ${delay}s">
                    <div>
                        <span class="badge ${levelClass}">${diag.level}</span>
                    </div>
                    <div class="diag-content">
                        <div class="diag-message">${diag.message}</div>
                        ${diag.line ? `<div class="diag-line">📍 Error at Line ${diag.line}</div>` : ''}
                    </div>
                </div>
            `;
        });

        resultsContent.innerHTML = html;
    }
});
