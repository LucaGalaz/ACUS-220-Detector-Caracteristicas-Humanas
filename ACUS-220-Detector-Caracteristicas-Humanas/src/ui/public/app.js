document.addEventListener('DOMContentLoaded', () => {
    // --- UI Elements ---
    const themeToggleBtn = document.getElementById('theme-toggle');
    const themeLabelLight = document.getElementById('theme-label-light');
    const themeLabelDark = document.getElementById('theme-label-dark');
    const brandLogo = document.getElementById('brand-logo');
    const htmlElement = document.documentElement;

    const btnRecord = document.getElementById('btn-record');
    const iconRecord = document.getElementById('icon-record');
    const btnUpload = document.getElementById('btn-upload');
    const iconUpload = document.getElementById('icon-upload');
    const fileInput = document.getElementById('file-input');
    const canvas = document.getElementById('audio-canvas');
    const ctx = canvas.getContext('2d');
    const loadingOverlay = document.getElementById('loading-overlay');
    const btnExport = document.getElementById('btn-export');

    const splashScreen = document.getElementById('splash-screen');
    const mainDashboard = document.getElementById('main-dashboard');
    const audioDock = document.getElementById('audio-dock');
    const btnEnterSplash = document.getElementById('btn-enter-splash');
    const brandText = document.getElementById('brand-text');

    // --- State ---
    let isRecording = false;
    let mediaRecorder = null;
    let audioChunks = [];
    let audioContext = null;
    let analyser = null;
    let animationId = null;
    let lastResults = null;
    
    // --- Background Animation Initialization ---
    let cleanupBackground = null;
    const bgContainer = document.getElementById('floating-lines-container');
    
    function startBackground() {
        if (!bgContainer || !window.initFloatingLines) return;
        
        if (cleanupBackground) {
            cleanupBackground();
            cleanupBackground = null;
        }
        
        const isLight = htmlElement.classList.contains('light-theme');
        
        cleanupBackground = window.initFloatingLines(bgContainer, {
            enabledWaves: ['top', 'middle', 'bottom'],
            lineCount: [10, 15, 20],
            lineDistance: [8, 6, 4],
            bendRadius: 5.0,
            bendStrength: -0.5,
            interactive: true,
            parallax: true,
            lightMode: isLight,
            backgroundColor: isLight ? '#e4eee4' : '#031704',
            linesGradient: isLight ? ['#2f681a', '#439b21', '#52a764'] : ['#1a4f10', '#3d7821', '#8eed4c']
        });
    }
    
    // Start background initially
    startBackground();

    // --- Theme Toggling ---
    function setTheme(isLight) {
        if (isLight) {
            htmlElement.classList.add('light-theme');
        } else {
            htmlElement.classList.remove('light-theme');
        }
        
        // Shadcn UI switch updates
        themeToggleBtn.setAttribute('aria-checked', !isLight); // true = dark
        if (isLight) {
            themeLabelLight.classList.add('active');
            themeLabelDark.classList.remove('active');
        } else {
            themeLabelLight.classList.remove('active');
            themeLabelDark.classList.add('active');
        }
        
        brandLogo.src = isLight ? 'assets/logo-black.svg' : 'assets/logo-white.svg';
        iconUpload.src = isLight ? 'assets/upload-file-black.svg' : 'assets/upload-file-white.svg';
        
        // Re-initialize background with new theme colors if splash is active
        if (!splashScreen.classList.contains('hidden')) {
            startBackground();
        }
    }

    themeToggleBtn.addEventListener('click', () => {
        const isLight = !htmlElement.classList.contains('light-theme');
        setTheme(isLight);
    });
    
    // Support clicking labels directly
    themeLabelLight.addEventListener('click', () => setTheme(true));
    themeLabelDark.addEventListener('click', () => setTheme(false));

    // --- Splash Screen Transition ---
    function enterDashboard() {
        if (!splashScreen.classList.contains('hidden')) {
            splashScreen.classList.add('hidden');
            mainDashboard.classList.remove('hidden');
            audioDock.classList.remove('hidden');
            brandText.classList.remove('hidden');
            
            // Clean up Background to save GPU/CPU resources on the dashboard
            if (cleanupBackground) {
                cleanupBackground();
                cleanupBackground = null;
            }
            
            resizeCanvas(); // Ensure canvas is sized correctly now that it's visible
            drawWaveform(); // Draw initial flat line
        }
    }

    btnEnterSplash.addEventListener('click', enterDashboard);
    
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            enterDashboard();
        }
    });

    // --- Canvas Resize ---
    function resizeCanvas() {
        const parent = canvas.parentElement;
        canvas.width = parent.clientWidth;
        canvas.height = parent.clientHeight;
    }
    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();

    // --- Waveform Animation ---
    function drawWaveform() {
        if (isRecording && analyser) {
            const bufferLength = analyser.frequencyBinCount;
            const dataArray = new Uint8Array(bufferLength);
            analyser.getByteTimeDomainData(dataArray);

            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.lineWidth = 2;
            ctx.strokeStyle = htmlElement.classList.contains('light-theme') ? '#439053' : '#52a764';
            ctx.beginPath();

            const sliceWidth = canvas.width * 1.0 / bufferLength;
            let x = 0;

            for (let i = 0; i < bufferLength; i++) {
                const v = dataArray[i] / 128.0;
                const y = v * canvas.height / 2;

                if (i === 0) {
                    ctx.moveTo(x, y);
                } else {
                    ctx.lineTo(x, y);
                }
                x += sliceWidth;
            }

            ctx.lineTo(canvas.width, canvas.height / 2);
            ctx.stroke();

            animationId = requestAnimationFrame(drawWaveform);
        } else {
            // Draw flat line when stopped or not yet started
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.lineWidth = 2;
            ctx.strokeStyle = htmlElement.classList.contains('light-theme') ? '#439053' : '#52a764';
            ctx.beginPath();
            ctx.moveTo(0, canvas.height / 2);
            ctx.lineTo(canvas.width, canvas.height / 2);
            ctx.stroke();
        }
    }

    // --- Audio Conversion Helper ---
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

        setUint32(0x46464952); // "RIFF"
        setUint32(length - 8); // file length - 8
        setUint32(0x45564157); // "WAVE"
        setUint32(0x20746d66); // "fmt " chunk
        setUint32(16); // length = 16
        setUint16(1); // PCM (uncompressed)
        setUint16(numOfChan);
        setUint32(buffer.sampleRate);
        setUint32(buffer.sampleRate * 2 * numOfChan); // avg. bytes/sec
        setUint16(numOfChan * 2); // block-align
        setUint16(16); // 16-bit
        setUint32(0x61746164); // "data" - chunk
        setUint32(length - pos - 4); // chunk length

        for (let i = 0; i < buffer.numberOfChannels; i++) {
            channels.push(buffer.getChannelData(i));
        }

        while (pos < length) {
            for (let i = 0; i < numOfChan; i++) {
                sample = Math.max(-1, Math.min(1, channels[i][offset])); // clamp
                sample = (0.5 + sample < 0 ? sample * 32768 : sample * 32767) | 0; // scale to 16-bit signed
                view.setInt16(pos, sample, true);
                pos += 2;
            }
            offset++;
        }
        return new Blob([bufferArray], { type: "audio/wav" });
    }

    async function convertBlobToWav(blob) {
        loadingOverlay.classList.remove('hidden'); // Show loading early
        const arrayBuffer = await blob.arrayBuffer();
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const audioBuffer = await ctx.decodeAudioData(arrayBuffer);
        const wavBlob = audioBufferToWav(audioBuffer);
        ctx.close();
        return wavBlob;
    }

    // --- Recording Logic ---
    async function startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const source = audioContext.createMediaStreamSource(stream);
            analyser = audioContext.createAnalyser();
            analyser.fftSize = 2048;
            source.connect(analyser);

            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];

            mediaRecorder.ondataavailable = e => {
                if (e.data.size > 0) audioChunks.push(e.data);
            };

            mediaRecorder.onstop = async () => {
                // Stop tracks
                stream.getTracks().forEach(track => track.stop());
                
                try {
                    const rawBlob = new Blob(audioChunks, { type: mediaRecorder.mimeType });
                    const wavBlob = await convertBlobToWav(rawBlob);
                    
                    if (audioContext) audioContext.close();
                    
                    await sendAudioToBackend(wavBlob, "recording.wav");
                } catch (err) {
                    console.error("Error convirtiendo audio:", err);
                    alert("Error al procesar la grabación. Intenta nuevamente.");
                    loadingOverlay.classList.add('hidden');
                }
            };

            mediaRecorder.start();
            isRecording = true;
            btnRecord.classList.add('is-recording');
            iconRecord.src = 'assets/pause-white.svg';
            drawWaveform();

        } catch (err) {
            console.error("Error accessing microphone:", err);
            alert("No se pudo acceder al micrófono. Por favor, permite el acceso en tu navegador.");
        }
    }

    function stopRecording() {
        if (mediaRecorder && mediaRecorder.state !== "inactive") {
            mediaRecorder.stop();
        }
        isRecording = false;
        btnRecord.classList.remove('is-recording');
        iconRecord.src = 'assets/play-white.svg';
        if (animationId) cancelAnimationFrame(animationId);
        drawWaveform(); // draw flat line
    }

    btnRecord.addEventListener('click', () => {
        if (isRecording) {
            stopRecording();
        } else {
            startRecording();
        }
    });

    // --- File Upload Logic ---
    btnUpload.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (file) {
            try {
                const wavBlob = await convertBlobToWav(file);
                await sendAudioToBackend(wavBlob, "upload.wav");
            } catch (err) {
                console.error("Error convirtiendo archivo:", err);
                alert("El archivo de audio no es válido o está corrupto.");
                loadingOverlay.classList.add('hidden');
            }
        }
        fileInput.value = ""; // Reset
    });

    // --- API Communication ---
    async function sendAudioToBackend(blob, filename) {
        loadingOverlay.classList.remove('hidden');
        btnExport.disabled = true;

        const formData = new FormData();
        formData.append('audio_file', blob, filename);

        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`Error HTTP: ${response.status}`);
            }

            const data = await response.json();
            lastResults = data;
            
            // Update UI
            document.getElementById('res-demographic').innerText = data.demographic_text;
            document.getElementById('res-physical').innerText = data.physical_text;
            document.getElementById('res-emotional').innerText = data.emotional_text;
            document.getElementById('res-diagnostic').innerText = data.diagnostic_text;
            
            btnExport.disabled = false;

        } catch (error) {
            console.error("API Error:", error);
            alert("Error al procesar el audio en el servidor.");
        } finally {
            loadingOverlay.classList.add('hidden');
        }
    }

    // --- Export ---
    btnExport.addEventListener('click', () => {
        if (!lastResults) return;
        
        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(lastResults.raw_json, null, 2));
        const downloadAnchorNode = document.createElement('a');
        downloadAnchorNode.setAttribute("href", dataStr);
        downloadAnchorNode.setAttribute("download", "reporte_acus220.json");
        document.body.appendChild(downloadAnchorNode);
        downloadAnchorNode.click();
        downloadAnchorNode.remove();
    });

    // Initial flat line
    drawWaveform();
});
