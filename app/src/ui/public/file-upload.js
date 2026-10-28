// Audio-only adaptation of the supplied upload card, hosted in a native dialog.
window.createAudioUpload = function ({ dialog, onSubmit }) {
    const find = (id) => dialog.querySelector(`#${id}`);
    const input = find('file-input');
    const frame = find('upload-drop-frame');
    const dropzone = find('upload-dropzone');
    const prompt = find('upload-prompt');
    const error = find('upload-error');
    const selection = find('upload-selection');
    const preview = find('upload-preview');
    const submit = find('upload-submit');
    const extensions = new Set(['wav', 'mp3', 'm4a', 'ogg', 'webm', 'flac', 'aac', 'opus', 'aiff', 'aif']);
    let selectedFile = null;
    let previewUrl = null;
    let dragDepth = 0;

    function resetDrag() {
        dragDepth = 0;
        frame.classList.remove('is-dragging');
        prompt.textContent = 'Arrastra tu audio aquí';
    }

    function clearSelection() {
        selectedFile = null;
        preview.pause();
        preview.removeAttribute('src');
        preview.load();
        if (previewUrl) URL.revokeObjectURL(previewUrl);
        previewUrl = null;
        input.value = '';
        selection.classList.add('hidden');
        submit.disabled = true;
    }

    function chooseFiles(files) {
        error.textContent = '';
        if (files.length !== 1) {
            error.textContent = 'Elige un solo audio a la vez.';
            return;
        }
        const file = files[0];
        const extension = file.name.split('.').pop().toLowerCase();
        if (!file.type.startsWith('audio/') && !extensions.has(extension)) {
            error.textContent = 'Ese archivo no es un audio. Prueba con un WAV, MP3, M4A u OGG.';
            return;
        }
        if (!file.size) {
            error.textContent = 'Este archivo está vacío. Elige otro audio.';
            return;
        }
        clearSelection();
        selectedFile = file;
        previewUrl = URL.createObjectURL(file);
        preview.src = previewUrl;
        find('upload-file-name').textContent = file.name;
        const unit = file.size < 1024 * 1024 ? 'KB' : 'MB';
        const size = file.size / (unit === 'KB' ? 1024 : 1024 * 1024);
        find('upload-file-size').textContent = `${Math.max(size, 0.1).toFixed(1)} ${unit} · Audio`;
        selection.classList.remove('hidden');
        submit.disabled = false;
    }

    dropzone.addEventListener('click', () => input.click());
    input.addEventListener('change', () => {
        if (input.files.length) chooseFiles(Array.from(input.files));
        input.value = '';
    });
    dropzone.addEventListener('dragenter', (event) => {
        event.preventDefault();
        dragDepth++;
        frame.classList.add('is-dragging');
        prompt.textContent = '¡Suéltalo y vamos!';
    });
    dropzone.addEventListener('dragleave', (event) => {
        event.preventDefault();
        dragDepth = Math.max(0, dragDepth - 1);
        if (!dragDepth) resetDrag();
    });
    dropzone.addEventListener('dragover', (event) => {
        event.preventDefault();
        event.dataTransfer.dropEffect = 'copy';
    });
    dropzone.addEventListener('drop', (event) => {
        event.preventDefault();
        resetDrag();
        if (event.dataTransfer.files.length) chooseFiles(Array.from(event.dataTransfer.files));
    });
    // Keep drops outside the target from navigating away from the app.
    dialog.addEventListener('dragover', (event) => event.preventDefault());
    dialog.addEventListener('drop', (event) => event.preventDefault());
    find('upload-remove').addEventListener('click', () => {
        clearSelection();
        error.textContent = '';
        dropzone.focus();
    });
    find('upload-cancel').addEventListener('click', () => dialog.close());
    dialog.addEventListener('keydown', (event) => {
        if (event.key !== 'Tab') return;
        const controls = Array.from(dialog.querySelectorAll('button:not(:disabled), audio[controls]'))
            .filter(control => control.getClientRects().length > 0);
        const first = controls[0];
        const last = controls[controls.length - 1];
        if (event.shiftKey && document.activeElement === first) {
            event.preventDefault();
            last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
            event.preventDefault();
            first.focus();
        }
    });
    dialog.addEventListener('click', (event) => {
        if (event.target !== dialog) return;
        const bounds = dialog.getBoundingClientRect();
        if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) dialog.close();
    });
    dialog.addEventListener('close', () => {
        clearSelection();
        resetDrag();
        error.textContent = '';
    });
    submit.addEventListener('click', () => {
        if (!selectedFile) return;
        const file = selectedFile;
        submit.disabled = true;
        dialog.close();
        onSubmit(file);
    });

    return {
        open() { if (!dialog.open) dialog.showModal(); },
        close() { if (dialog.open) dialog.close(); },
        showError(message) { if (!dialog.open) dialog.showModal(); error.textContent = message; },
    };
};
