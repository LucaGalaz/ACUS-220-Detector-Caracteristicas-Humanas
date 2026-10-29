document.addEventListener('DOMContentLoaded', () => {

    const themeToggleBtn = document.getElementById('theme-toggle');
    const themeIconSun = document.getElementById('theme-icon-sun');
    const themeIconMoon = document.getElementById('theme-icon-moon');
    const brandLogo = document.getElementById('brand-logo');
    const htmlElement = document.documentElement;

    const btnRecord = document.getElementById('btn-record');
    const iconRecord = document.getElementById('icon-record');
    const btnUpload = document.getElementById('btn-upload');
    const loadingOverlay = document.getElementById('loading-overlay');
    const btnExport = document.getElementById('btn-export');

    const splashScreen = document.getElementById('splash-screen');
    const mainDashboard = document.getElementById('main-dashboard');
    const resultsGrid = document.getElementById('results-grid');
    const workspaceStage = document.getElementById('workspace-stage');
    const workspaceEmpty = document.getElementById('workspace-empty');
    const workspaceStageTitle = document.getElementById('workspace-stage-title');
    const workspaceStageDescription = document.getElementById('workspace-stage-description');
    const recordingLevel = document.getElementById('recording-level');
    const audioDock = document.getElementById('audio-dock');
    const btnEnterSplash = document.getElementById('btn-enter-splash');
    const brandText = document.getElementById('brand-text');
    const brandHome = document.getElementById('brand-home');
    const recordingReview = document.getElementById('recording-review');
    const recordingPreview = document.getElementById('recording-preview');
    const recordingError = document.getElementById('recording-error');
    const btnDiscardRecording = document.getElementById('recording-discard');
    const btnAnalyzeRecording = document.getElementById('recording-analyze');

    let isRecording = false;
    let mediaRecorder = null;
    let lastResults = null;
    let themeTransitionRunning = false;
    let recordingGeneration = 0;
    let recordingState = 'idle';
    let recordingStream = null;
    let pendingRecording = null;
    let isAnalyzing = false;
    let revealResultsPending = false;
    let resultAnimations = [];
    let audioTextFeedback = null;
    let lastAnalysisError = '';
    const uploadPanel = window.createAudioUpload({
        dialog: document.getElementById('upload-dialog'),
        onSubmit: processUploadedFile,
    });

    function setTheme(isLight) {
        htmlElement.classList.toggle('light-theme', isLight);
        htmlElement.classList.toggle('dark-theme', !isLight);

        themeToggleBtn.setAttribute('aria-checked', !isLight);
        themeToggleBtn.title = isLight ? 'Cambiar a modo oscuro' : 'Cambiar a modo claro';
        themeIconSun.classList.toggle('hidden', isLight);
        themeIconMoon.classList.toggle('hidden', !isLight);

        brandLogo.src = isLight ? 'assets/logo-black.svg' : 'assets/logo-white.svg';
        try {
            localStorage.setItem('theme', isLight ? 'light' : 'dark');
        } catch {}
    }

    async function toggleTheme() {
        if (themeTransitionRunning) return;
        const isLight = !htmlElement.classList.contains('light-theme');
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            setTheme(isLight);
            return;
        }
        if (!document.startViewTransition) {
            themeTransitionRunning = true;
            htmlElement.classList.add('theme-fading');

            getComputedStyle(document.body).backgroundColor;
            setTheme(isLight);
            window.setTimeout(() => {
                htmlElement.classList.remove('theme-fading');
                themeTransitionRunning = false;
            }, 450);
            return;
        }

        const { left, top, width, height } = themeToggleBtn.getBoundingClientRect();
        const centerX = left + width / 2;
        const centerY = top + height / 2;
        const radius = Math.hypot(
            Math.max(centerX, window.innerWidth - centerX),
            Math.max(centerY, window.innerHeight - centerY),
        );
        themeTransitionRunning = true;
        themeToggleBtn.setAttribute('aria-busy', 'true');
        htmlElement.classList.add('theme-transitioning');
        let transition;
        try {
            transition = document.startViewTransition(() => setTheme(isLight));
            await transition.ready;
            await htmlElement.animate(
                {
                    clipPath: [`circle(0px at ${centerX}px ${centerY}px)`, `circle(${radius}px at ${centerX}px ${centerY}px)`],
                    filter: ['brightness(0.85)', 'brightness(1)'],
                },
                { duration: 900, easing: 'ease-in-out', pseudoElement: '::view-transition-new(root)' },
            ).finished;
            await transition.finished;
        } catch {
            transition?.skipTransition();
            setTheme(isLight);
        } finally {
            htmlElement.classList.remove('theme-transitioning');
            themeToggleBtn.removeAttribute('aria-busy');
            themeTransitionRunning = false;
        }
    }

    themeToggleBtn.addEventListener('click', toggleTheme);

    function enterDashboard() {
        if (!splashScreen.classList.contains('hidden')) {
            splashScreen.classList.add('hidden');
            mainDashboard.classList.remove('hidden');
            audioDock.classList.remove('hidden');
            brandText.classList.remove('hidden');
            syncRecordingUI();

            (pendingRecording ? recordingReview : btnRecord).focus({ preventScroll: true });
        }
    }

    btnEnterSplash.addEventListener('click', (event) => {
        if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            const bounds = btnEnterSplash.getBoundingClientRect();
            const ripple = document.createElement('span');
            const size = Math.max(bounds.width, bounds.height);
            ripple.className = 'vh-button-ripple';
            ripple.setAttribute('aria-hidden', 'true');
            ripple.style.width = ripple.style.height = `${size}px`;
            ripple.style.left = `${(event.detail ? event.clientX - bounds.left : bounds.width / 2) - size / 2}px`;
            ripple.style.top = `${(event.detail ? event.clientY - bounds.top : bounds.height / 2) - size / 2}px`;
            ripple.addEventListener('animationend', () => ripple.remove(), { once: true });
            window.setTimeout(() => ripple.remove(), 650);
            btnEnterSplash.appendChild(ripple);
        }
        enterDashboard();
    });

    brandHome.addEventListener('click', () => {
        if (!splashScreen.classList.contains('hidden')) return;
        recordingGeneration++;
        if (['starting', 'requesting', 'recording', 'stopping'].includes(recordingState)) {
            if (mediaRecorder && mediaRecorder.state !== 'inactive') mediaRecorder.stop();
            recordingStream?.getTracks().forEach(track => track.stop());
            setRecordingState(pendingRecording ? 'review' : 'idle');
        }
        recordingPreview.pause();
        uploadPanel.close();
        mainDashboard.classList.add('hidden');
        audioDock.classList.add('hidden');
        brandText.classList.add('hidden');
        splashScreen.classList.remove('hidden');
        syncRecordingUI();
        btnEnterSplash.focus({ preventScroll: true });
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && e.target === document.body) {
            enterDashboard();
        }
    });

    function audioBufferToWav(buffer) {
        let numOfChan = buffer.numberOfChannels;
        let length = buffer.length * numOfChan * 2 + 44;
        let bufferArray = new ArrayBuffer(length);
        let view = new DataView(bufferArray);
        let channels = [];
        let sample = 0;
        let offset = 0;
        let pos = 0;

        function setUint16(data) { view.setUint16(pos, data, true); pos += 2; }
        function setUint32(data) { view.setUint32(pos, data, true); pos += 4; }

        setUint32(0x46464952);
        setUint32(length - 8);
        setUint32(0x45564157);
        setUint32(0x20746d66);
        setUint32(16);
        setUint16(1);
        setUint16(numOfChan);
        setUint32(buffer.sampleRate);
        setUint32(buffer.sampleRate * 2 * numOfChan);
        setUint16(numOfChan * 2);
        setUint16(16);
        setUint32(0x61746164);
        setUint32(length - pos - 4);

        for (let i = 0; i < buffer.numberOfChannels; i++) {
            channels.push(buffer.getChannelData(i));
        }

        while (pos < length) {
            for (let i = 0; i < numOfChan; i++) {
                sample = Math.max(-1, Math.min(1, channels[i][offset]));
                sample = Math.round(sample < 0 ? sample * 32768 : sample * 32767);
                view.setInt16(pos, sample, true);
                pos += 2;
            }
            offset++;
        }
        return new Blob([bufferArray], { type: "audio/wav" });
    }

    async function convertBlobToWav(blob) {
        if (blob.size > 25 * 1024 * 1024) throw new Error('El audio supera el límite de 25 MB.');
        isAnalyzing = true;
        loadingOverlay.classList.remove('hidden');
        syncRecordingUI();
        const arrayBuffer = await blob.arrayBuffer();
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        try {
            const audioBuffer = await ctx.decodeAudioData(arrayBuffer);
            if (audioBuffer.duration < 1 || audioBuffer.duration > 120) {
                throw new Error('Usa un audio de 1 a 120 segundos. Para mejores resultados, graba 6–10 segundos de habla.');
            }
            return audioBufferToWav(audioBuffer);
        } finally {
            await ctx.close();
        }
    }

    function isAudioBusy() {
        return isAnalyzing || ['stopping', 'analyzing'].includes(recordingState);
    }

    function syncWorkView() {
        const inWorkspace = !mainDashboard.classList.contains('hidden');
        const busy = isAudioBusy();
        const showResults = inWorkspace && Boolean(lastResults) && recordingState === 'idle' && !busy;
        const showReview = inWorkspace && Boolean(pendingRecording) && !busy;
        resultsGrid.classList.toggle('hidden', !showResults);
        workspaceStage.classList.toggle('hidden', !inWorkspace || showResults);
        recordingReview.classList.toggle('hidden', !showReview);
        workspaceEmpty.classList.toggle('hidden', !inWorkspace || showResults || showReview || busy);

        const stageMessages = {
            idle: ['Todo empieza con la voz', 'Graba un audio o sube un archivo para descubrirlo.'],
            starting: ['Te escuchamos…', ''],
            requesting: ['Permite el micrófono', 'Acepta el permiso en el navegador para empezar a grabar.'],
            blocked: ['Permite el micrófono', 'Revisa su permiso en el navegador y vuelve a intentarlo.'],
            recording: ['Te escuchamos…', ''],
        };
        const message = stageMessages[recordingState];
        if (message && !workspaceEmpty.classList.contains('hidden')) {
            if (workspaceStageTitle.textContent !== message[0]) workspaceStageTitle.textContent = message[0];
            if (workspaceStageDescription.textContent !== message[1]) workspaceStageDescription.textContent = message[1];
            workspaceStageDescription.classList.toggle('hidden', !message[1]);
        }

        if (!showResults) {
            resultAnimations.forEach(animation => animation.cancel());
            resultAnimations = [];
        } else if (revealResultsPending) {
            revealResultsPending = false;
            mainDashboard.scrollTop = 0;
            if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
                resultAnimations = Array.from(resultsGrid.querySelectorAll('.vh-card')).map(card => card.animate(
                    [{ opacity: 0, transform: 'translateY(14px) scale(0.97)' }, { opacity: 1, transform: 'translateY(0) scale(1)' }],
                    { duration: 420, easing: 'cubic-bezier(0.2, 0.8, 0.2, 1)' },
                ));
            }
        }
    }

    function finishAnalysis() {
        isAnalyzing = false;
        loadingOverlay.classList.add('hidden');
        syncRecordingUI();
    }

    function syncRecordingUI() {
        isRecording = recordingState === 'recording';
        const busy = isAudioBusy();
        loadingOverlay.classList.toggle('hidden', !busy);
        loadingOverlay.setAttribute('aria-label', recordingState === 'stopping' ? 'Preparando grabación' : 'Analizando audio');
        mainDashboard.setAttribute('aria-busy', String(busy));
        if (!isRecording && audioTextFeedback) {
            audioTextFeedback.stop();
            audioTextFeedback = null;
        }
        btnRecord.disabled = isAnalyzing || !['idle', 'blocked', 'recording'].includes(recordingState);
        btnUpload.disabled = isAnalyzing || !['idle', 'blocked'].includes(recordingState);
        btnRecord.classList.toggle('is-recording', isRecording);
        btnRecord.setAttribute('aria-label', isRecording ? 'Detener grabación' : 'Grabar');
        iconRecord.src = isRecording ? 'assets/stop-white.svg' : 'assets/microphone-white.svg';
        iconRecord.alt = isRecording ? 'Detener grabación' : 'Grabar';
        syncWorkView();
        btnAnalyzeRecording.disabled = isAnalyzing || recordingState === 'analyzing';
        btnDiscardRecording.disabled = isAnalyzing || recordingState === 'analyzing';
    }

    function setRecordingState(state) {
        recordingState = state;
        syncRecordingUI();
    }

    function clearPendingRecording() {
        recordingPreview.pause();
        recordingPreview.removeAttribute('src');
        recordingPreview.load();
        if (pendingRecording) URL.revokeObjectURL(pendingRecording.url);
        pendingRecording = null;
        recordingError.textContent = '';
    }

    async function getMicrophonePermission() {
        try {
            const permission = await navigator.permissions?.query({ name: 'microphone' });
            return permission?.state || 'unknown';
        } catch {

            return 'unknown';
        }
    }

    async function startRecording() {
        if (!['idle', 'blocked'].includes(recordingState)) return;
        const generation = ++recordingGeneration;
        let stream = null;
        setRecordingState('starting');
        try {
            const permission = await getMicrophonePermission();
            if (generation !== recordingGeneration || mainDashboard.classList.contains('hidden')) return;
            if (permission === 'denied') {
                setRecordingState('blocked');
                return;
            }

            if (permission === 'prompt') setRecordingState('requesting');
            stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            if (generation !== recordingGeneration || mainDashboard.classList.contains('hidden')) {
                stream.getTracks().forEach(track => track.stop());
                return;
            }
            recordingStream = stream;
            const recorder = new MediaRecorder(stream);
            mediaRecorder = recorder;
            const chunks = [];
            const startedAt = performance.now();
            recorder.ondataavailable = event => {
                if (event.data.size > 0) chunks.push(event.data);
            };
            recorder.onstop = () => {
                stream.getTracks().forEach(track => track.stop());
                try {
                    if (generation !== recordingGeneration) return;
                    const blob = new Blob(chunks, { type: recorder.mimeType });
                    if (!blob.size) throw new Error('Empty recording');
                    pendingRecording = { blob, url: URL.createObjectURL(blob) };
                    recordingPreview.src = pendingRecording.url;
                    const seconds = Math.max(1, Math.round((performance.now() - startedAt) / 1000));
                    document.getElementById('recording-duration').textContent = `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`;
                    recordingError.textContent = '';
                    setRecordingState('review');
                    recordingReview.focus({ preventScroll: true });
                } catch (error) {
                    if (generation === recordingGeneration) {
                        setRecordingState('idle');
                        alert('No pudimos guardar la grabación. Intenta grabar de nuevo.');
                    }
                } finally {
                    if (recordingStream === stream) recordingStream = null;
                }
            };
            recorder.onerror = () => {
                stream.getTracks().forEach(track => track.stop());
                if (generation === recordingGeneration) {
                    recordingGeneration++;
                    setRecordingState('idle');
                    alert('La grabación se interrumpió. Intenta de nuevo.');
                }
            };
            recorder.start();
            setRecordingState('recording');
            audioTextFeedback = window.createAudioTextFeedback(workspaceStageTitle, stream, recordingLevel);
        } catch (error) {
            stream?.getTracks().forEach(track => track.stop());
            if (generation === recordingGeneration) {
                if (['NotAllowedError', 'SecurityError'].includes(error.name)) {
                    setRecordingState('blocked');
                } else {
                    setRecordingState('idle');
                    alert('No se pudo iniciar el micrófono. Comprueba que esté conectado y disponible.');
                }
            }
        }
    }

    function stopRecording() {
        if (recordingState !== 'recording') return;
        setRecordingState('stopping');
        mediaRecorder.stop();
        recordingStream?.getTracks().forEach(track => track.stop());
    }

    btnRecord.addEventListener('click', () => {
        if (isRecording) stopRecording();
        else startRecording();
    });

    btnDiscardRecording.addEventListener('click', () => {
        clearPendingRecording();
        setRecordingState('idle');
        btnRecord.focus();
    });

    btnAnalyzeRecording.addEventListener('click', async () => {
        if (!pendingRecording || recordingState !== 'review') return;
        const recording = pendingRecording;
        recordingPreview.pause();
        recordingError.textContent = '';
        setRecordingState('analyzing');
        try {
            const wavBlob = await convertBlobToWav(recording.blob);
            const success = await sendAudioToBackend(wavBlob, 'recording.wav');
            if (success) {
                clearPendingRecording();
                setRecordingState('idle');
                if (!mainDashboard.classList.contains('hidden')) btnRecord.focus();
            } else {
                recordingError.textContent = `${lastAnalysisError} Tu grabación sigue aquí para volver a intentarlo.`;
                setRecordingState('review');
            }
        } catch (error) {
            recordingError.textContent = error.message || 'No pudimos leer la grabación. Puedes escucharla, descartarla o volver a intentarlo.';
            setRecordingState('review');
        } finally {
            finishAnalysis();
        }
    });

    btnUpload.addEventListener('click', () => uploadPanel.open());

    async function processUploadedFile(file) {
        try {
            const wavBlob = await convertBlobToWav(file);
            const success = await sendAudioToBackend(wavBlob, 'upload.wav');
            if (!success) uploadPanel.showError(lastAnalysisError, file);
        } catch (err) {
            console.error('Error convirtiendo archivo:', err);
            loadingOverlay.classList.add('hidden');
            const message = err.name === 'EncodingError' ? 'No pudimos leer ese audio. Prueba con otro archivo.' : err.message;
            uploadPanel.showError(message || 'No pudimos leer ese audio. Prueba con otro archivo.', file);
        } finally {
            finishAnalysis();
        }
    }

    async function sendAudioToBackend(blob, filename) {
        lastAnalysisError = '';
        isAnalyzing = true;
        loadingOverlay.classList.remove('hidden');
        syncRecordingUI();
        btnExport.disabled = true;

        const formData = new FormData();
        formData.append('audio_file', blob, filename);

        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const problem = await response.json().catch(() => ({}));
                throw new Error(typeof problem.detail === 'string' ? problem.detail : 'No se pudo completar el análisis del audio.');
            }

            const data = await response.json();
            const textFields = ['demographic_text', 'physical_text', 'emotional_text', 'diagnostic_text'];
            if (!textFields.every(field => typeof data[field] === 'string' && data[field].trim())) {
                throw new Error('El análisis no devolvió todos los resultados.');
            }
            lastResults = data;

            document.getElementById('res-demographic').textContent = data.demographic_text;
            document.getElementById('res-physical').textContent = data.physical_text;
            document.getElementById('res-emotional').textContent = data.emotional_text;
            document.getElementById('res-diagnostic').textContent = data.diagnostic_text;
            revealResultsPending = true;

            btnExport.disabled = false;
            return true;

        } catch (error) {
            console.error("API Error:", error);
            lastAnalysisError = error.name === 'TypeError' ? 'No se pudo contactar con el servidor.' : error.message;
            btnExport.disabled = !lastResults;
            return false;
        } finally {
            finishAnalysis();
        }
    }

    btnExport.addEventListener('click', () => {
        if (!lastResults) return;

        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(lastResults.raw_json, null, 2));
        const downloadAnchorNode = document.createElement('a');
        downloadAnchorNode.setAttribute("href", dataStr);
        const now = new Date();
        const pad = value => String(value).padStart(2, '0');
        const date = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
        const time = `${pad(now.getHours())}-${pad(now.getMinutes())}-${pad(now.getSeconds())}`;
        downloadAnchorNode.setAttribute('download', `Voihunt_${date}_${time}.json`);
        document.body.appendChild(downloadAnchorNode);
        downloadAnchorNode.click();
        downloadAnchorNode.remove();
    });

    let initialLight = htmlElement.classList.contains('light-theme');
    try {
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'light' || savedTheme === 'dark') initialLight = savedTheme === 'light';
    } catch {}
    setTheme(initialLight);
    syncRecordingUI();
});
