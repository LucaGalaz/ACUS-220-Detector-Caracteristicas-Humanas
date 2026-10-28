// The text follows the captured signal; no output is connected to the speakers.
window.createAudioTextFeedback = function (element, stream) {
    let context;
    let source;
    let analyser;
    let frame = null;
    let active = true;
    const text = element.textContent;
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    const letters = [];
    const offsets = [];
    let energy = 0;
    let lastPaint = 0;

    function stop() {
        active = false;
        if (frame !== null) cancelAnimationFrame(frame);
        source?.disconnect();
        analyser?.disconnect();
        if (context && context.state !== 'closed') context.close().catch(() => {});
        element.classList.remove('vh-audio-reactive');
        element.style.removeProperty('--vh-audio-energy');
        element.style.removeProperty('transform');
        element.removeAttribute('aria-label');
        if (letters.length) element.textContent = text;
    }

    try {
        context = new (window.AudioContext || window.webkitAudioContext)();
        source = context.createMediaStreamSource(stream);
        analyser = context.createAnalyser();
        analyser.fftSize = 1024;
        source.connect(analyser);
        if (context.state === 'suspended') context.resume().catch(() => {});
        const samples = new Float32Array(analyser.fftSize);
        const fragment = document.createDocumentFragment();
        for (const character of text) {
            const letter = document.createElement('span');
            letter.className = 'vh-voice-letter';
            letter.textContent = character;
            letter.setAttribute('aria-hidden', 'true');
            fragment.appendChild(letter);
            letters.push(letter);
            offsets.push(0);
        }
        element.replaceChildren(fragment);
        element.setAttribute('aria-label', text);
        element.classList.add('vh-audio-reactive');

        function paint(timestamp) {
            if (!active) return;
            if (timestamp - lastPaint >= 32 && !document.hidden) {
                analyser.getFloatTimeDomainData(samples);
                let sum = 0;
                for (const sample of samples) sum += sample * sample;
                const rms = Math.sqrt(sum / samples.length);
                const target = Math.min(1, Math.max(0, rms - 0.004) * 12);
                energy += (target - energy) * (target > energy ? 0.6 : 0.25);
                if (energy < 0.001) energy = 0;
                element.style.setProperty('--vh-audio-energy', energy.toFixed(4));
                element.style.transform = reducedMotion.matches ? 'none' : `scale(${(1 + energy * 0.035).toFixed(4)})`;
                letters.forEach((letter, index) => {
                    const sample = samples[Math.floor(index / Math.max(1, letters.length - 1) * (samples.length - 1))];
                    const targetOffset = reducedMotion.matches ? 0 : -Math.max(-1, Math.min(1, sample * 3)) * energy * 6;
                    offsets[index] += (targetOffset - offsets[index]) * 0.5;
                    letter.style.transform = reducedMotion.matches ? 'none' : `translateY(${offsets[index].toFixed(2)}px)`;
                });
                lastPaint = timestamp;
            }
            frame = requestAnimationFrame(paint);
        }
        frame = requestAnimationFrame(paint);
    } catch {
        // Capturing audio must still work if visual feedback is unavailable.
        stop();
    }
    return { stop };
};
