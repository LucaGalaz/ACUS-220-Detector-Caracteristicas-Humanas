window.createAudioTextFeedback = function (element, stream, meter = null) {
    let context;
    let source;
    let analyser;
    let frame = null;
    let active = true;
    let lastPaint = 0;
    const floorDb = -72;
    const segmentCount = 24;
    const segments = [];

    function setLevel(db) {
        const level = (db - floorDb) / -floorDb;
        const count = Math.round(level * segmentCount);
        segments.forEach((segment, index) => segment.classList.toggle('is-active', index < count));
        element.style.setProperty('--vh-audio-energy', level.toFixed(4));
        meter?.setAttribute('aria-valuenow', db.toFixed(1));
        meter?.setAttribute('aria-valuetext', db === floorDb ? 'Sin señal' : `${Math.round(db)} dB`);
    }

    function stop() {
        active = false;
        if (frame !== null) cancelAnimationFrame(frame);
        source?.disconnect();
        analyser?.disconnect();
        if (context && context.state !== 'closed') context.close().catch(() => {});
        setLevel(floorDb);
        element.classList.remove('vh-audio-reactive');
        element.style.removeProperty('--vh-audio-energy');
        meter?.classList.add('hidden');
    }

    try {
        context = new (window.AudioContext || window.webkitAudioContext)();
        source = context.createMediaStreamSource(stream);
        analyser = context.createAnalyser();
        analyser.fftSize = 1024;
        source.connect(analyser);
        if (context.state === 'suspended') context.resume().catch(() => {});
        const samples = new Float32Array(analyser.fftSize);
        const container = meter?.querySelector('.vh-level-segments');
        if (container) {
            const fragment = document.createDocumentFragment();
            for (let index = 0; index < segmentCount; index++) {
                const segment = document.createElement('span');
                segment.className = 'vh-level-segment';
                segments.push(segment);
                fragment.appendChild(segment);
            }
            container.replaceChildren(fragment);
        }
        setLevel(floorDb);
        element.classList.add('vh-audio-reactive');
        meter?.classList.remove('hidden');

        function paint(timestamp) {
            if (!active) return;
            if (timestamp - lastPaint >= 32 && !document.hidden) {
                analyser.getFloatTimeDomainData(samples);
                let sum = 0;
                for (const sample of samples) sum += sample * sample;
                const rms = Math.sqrt(sum / samples.length);
                const db = rms > 0 ? Math.max(floorDb, Math.min(0, 20 * Math.log10(rms))) : floorDb;
                setLevel(db);
                lastPaint = timestamp;
            }
            frame = requestAnimationFrame(paint);
        }
        frame = requestAnimationFrame(paint);
    } catch {

        stop();
    }
    return { stop };
};
