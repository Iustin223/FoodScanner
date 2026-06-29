const form = document.getElementById('uploadForm');

if (form) {
    const fileInput = document.getElementById('fileInput');
    const resultsDiv = document.getElementById('results');
    const previewImg = document.getElementById('preview');
    const uploadPrompt = document.getElementById('uploadPrompt');
    const dropZone = document.getElementById('dropZone');
    const scanBtn = document.getElementById('scanBtn');
    const clearBtn = document.getElementById('clearBtn');

    // Store the selected file here — works for both click and drag
    let selectedFile = null;

    // Show preview when file selected via click
    fileInput.addEventListener('change', function() {
        const file = this.files[0];
        if (file) {
            selectedFile = file;
            showPreview(file);
        }
    });

    function showPreview(file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            previewImg.src = e.target.result;
            previewImg.style.display = 'block';
            uploadPrompt.style.display = 'none';
            clearBtn.style.display = 'block';
        };
        reader.readAsDataURL(file);
    }

    // Clear button
    clearBtn.addEventListener('click', function() {
        selectedFile = null;
        fileInput.value = '';
        previewImg.style.display = 'none';
        previewImg.src = '';
        uploadPrompt.style.display = 'flex';
        clearBtn.style.display = 'none';
        resultsDiv.innerHTML = '';
    });

    // Drag and drop
    dropZone.addEventListener('dragover', function(e) {
        e.preventDefault();
        this.classList.add('drag-over');
    });

    dropZone.addEventListener('dragleave', function() {
        this.classList.remove('drag-over');
    });

    dropZone.addEventListener('drop', function(e) {
        e.preventDefault();
        this.classList.remove('drag-over');
        const file = e.dataTransfer.files[0];
        if (file) {
            selectedFile = file;
            showPreview(file);
        }
    });

    // Handle form submission
    form.addEventListener('submit', async function(event) {
        event.preventDefault();

        // Use selectedFile instead of fileInput.files[0]
        if (!selectedFile) {
            alert('Selectează o imagine!');
            return;
        }

        scanBtn.disabled = true;
        scanBtn.textContent = ' Se procesează...';
        resultsDiv.innerHTML = `
            <div class="loading">
                <p>Se analizează imaginea...</p>
                <p>Aceasta poate dura 10-30 secunde.</p>
            </div>
        `;

        const formData = new FormData();
        formData.append('file', selectedFile);

        const token = localStorage.getItem('token');
        const headers = {};

        if(token)
        {
            headers['Authorization'] = 'Bearer ' + token;
        }

        try {
            const response = await fetch('/scan', {
                method: 'POST',
                headers: headers,
                body: formData
            });

            const data = await response.json();

            if (data.error && (!data.ingredients || data.ingredients.length === 0)) {
                resultsDiv.innerHTML = `<div class="error-msg">${data.error}</div>`;
                return;
            }

            displayResults(data);

        } catch (error) {
            resultsDiv.innerHTML = `<div class="error-msg">Eroare de conexiune: ${error.message}</div>`;
        } finally {
            scanBtn.disabled = false;
            scanBtn.textContent = '⌘ Scanează';
        }
    });

    function displayResults(data) {
        let html = '';

        const s = data.summary;
        html += '<div class="summary-bar">';
        if (s.periculos > 0) html += `<span class="badge badge-danger"><i class="fa-solid fa-face-angry fa-sm" style="color: rgb(233, 22, 22);"></i> ${s.periculos} periculoase</span>`;
        if (s.moderat > 0) html += `<span class="badge badge-warning"><i class="fa-solid fa-face-meh fa-sm" style="color: rgb(233, 187, 22);"></i> ${s.moderat} moderate</span>`;
        if (s.inofensiv > 0) html += `<span class="badge badge-safe"><i class="fa-solid fa-face-grin-beam fa-sm" style="color: rgb(51, 172, 45);"></i> ${s.inofensiv} inofensive</span>`;
        if (s.necunoscut > 0) html += `<span class="badge badge-unknown"><i class="fa-regular fa-face-meh-blank fa-sm" style="color: rgb(109, 120, 118);"></i> ${s.necunoscut} necunoscute</span>`;
        html += '</div>';

        html += '<div class="ingredients-grid">';

        const order = {'periculos': 0, 'moderat': 1, 'inofensiv': 2, 'necunoscut': 3};
        const sorted = [...data.ingredients].sort((a, b) => {
            return (order[a.risc] || 3) - (order[b.risc] || 3);
        });

        for (const item of sorted) {
            const riskClass = {
                'periculos': 'card-danger',
                'moderat': 'card-warning',
                'inofensiv': 'card-safe',
                'necunoscut': 'card-unknown'
            }[item.risc] || 'card-unknown';

            const emoji = {
                'periculos': '<i class="fa-solid fa-face-angry fa-lg" style="color: rgb(233, 22, 22);"></i>',
                'moderat': '<i class="fa-solid fa-face-meh fa-lg" style="color: rgb(233, 187, 22);"></i>',
                'inofensiv': '<i class="fa-solid fa-face-grin-beam fa-lg" style="color: rgb(51, 172, 45);"></i>',
                'necunoscut': '<i class="fa-regular fa-face-meh-blank fa-lg" style="color: rgb(109, 120, 118);"></i>'
            }[item.risc] || '<i class="fa-regular fa-face-meh-blank fa-lg" style="color: rgb(109, 120, 118);"></i>';

            const name = item.matched || item.ingredient;

            const code = item.cod_e && item.cod_e !== '-' && item.cod_e !== 'None' && item.cod_e !== 'nan'
                         ? `<span class="e-code">${item.cod_e}</span>` : '';

            html += `
                <div class="ingredient-card ${riskClass}">
                    <div class="ingredient-header">
                        <span>${emoji}</span>
                        <strong>${name}</strong>
                        ${code}
                    </div>
                    <div class="ingredient-desc">${item.descriere || ''}</div>
                </div>`;
        }

        html += '</div>';
        resultsDiv.innerHTML = html;
    }

}