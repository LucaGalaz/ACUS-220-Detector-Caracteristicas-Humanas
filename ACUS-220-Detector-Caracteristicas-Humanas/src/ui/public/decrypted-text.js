// DecryptedText Component - Vanilla JS Port
function initDecryptedText(element, options = {}) {
  const text = element.getAttribute('data-text') || element.textContent.trim();
  element.setAttribute('data-text', text); // save original
  element.innerHTML = ''; // clear
  
  const speed = options.speed ?? 50;
  const maxIterations = options.maxIterations ?? 10;
  const sequential = options.sequential ?? false;
  const revealDirection = options.revealDirection ?? 'start';
  const useOriginalCharsOnly = options.useOriginalCharsOnly ?? false;
  const characters = options.characters ?? 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!@#$%^&*()_+';
  const className = options.className ?? '';
  const encryptedClassName = options.encryptedClassName ?? 'encrypted';
  const animateOn = options.animateOn ?? 'hover'; // 'hover', 'view', etc.
  
  const availableChars = useOriginalCharsOnly
      ? Array.from(new Set(text.split(''))).filter(char => char !== ' ')
      : characters.split('');
      
  const spans = [];
  for (let i = 0; i < text.length; i++) {
    const span = document.createElement('span');
    span.textContent = text[i];
    element.appendChild(span);
    spans.push(span);
  }
  
  let interval = null;
  let isAnimating = false;
  
  function shuffleText(revealedIndices) {
    for (let i = 0; i < text.length; i++) {
      if (text[i] === ' ') {
        spans[i].textContent = ' ';
        continue;
      }
      if (revealedIndices.has(i)) {
        spans[i].textContent = text[i];
        if (className) spans[i].className = className;
        else spans[i].removeAttribute('class');
      } else {
        spans[i].textContent = availableChars[Math.floor(Math.random() * availableChars.length)];
        if (encryptedClassName) spans[i].className = encryptedClassName;
      }
    }
  }
  
  function computeOrder(len) {
    const order = [];
    if (len <= 0) return order;
    if (revealDirection === 'start') {
      for (let i = 0; i < len; i++) order.push(i);
      return order;
    }
    if (revealDirection === 'end') {
      for (let i = len - 1; i >= 0; i--) order.push(i);
      return order;
    }
    // center
    const middle = Math.floor(len / 2);
    let offset = 0;
    while (order.length < len) {
      if (offset % 2 === 0) {
        const idx = middle + offset / 2;
        if (idx >= 0 && idx < len) order.push(idx);
      } else {
        const idx = middle - Math.ceil(offset / 2);
        if (idx >= 0 && idx < len) order.push(idx);
      }
      offset++;
    }
    return order.slice(0, len);
  }
  
  function triggerDecrypt() {
    if (isAnimating) return;
    isAnimating = true;
    
    let revealedIndices = new Set();
    let currentIteration = 0;
    
    if (interval) clearInterval(interval);
    
    if (sequential) {
      const order = computeOrder(text.length);
      interval = setInterval(() => {
        if (revealedIndices.size < text.length) {
          revealedIndices.add(order[revealedIndices.size]);
          shuffleText(revealedIndices);
        } else {
          clearInterval(interval);
          isAnimating = false;
        }
      }, speed);
    } else {
      interval = setInterval(() => {
        shuffleText(revealedIndices);
        currentIteration++;
        if (currentIteration >= maxIterations) {
          clearInterval(interval);
          isAnimating = false;
          // Reveal all
          for (let i = 0; i < text.length; i++) revealedIndices.add(i);
          shuffleText(revealedIndices);
        }
      }, speed);
    }
  }
  
  function resetToPlainText() {
    if (interval) clearInterval(interval);
    isAnimating = false;
    let s = new Set();
    for (let i = 0; i < text.length; i++) s.add(i);
    shuffleText(s);
  }
  
  // Event listeners
  if (animateOn === 'hover') {
    element.addEventListener('mouseenter', triggerDecrypt);
    // element.addEventListener('mouseleave', resetToPlainText);
  }
  
  // Animate once on load if needed
  if (animateOn === 'view' || animateOn === 'hover') {
      setTimeout(() => triggerDecrypt(), 100);
  }

  let loopTimer = null;
  if (options.loopInterval) {
      loopTimer = setInterval(() => {
          triggerDecrypt();
      }, options.loopInterval);
  }

  return () => {
    if (interval) clearInterval(interval);
    if (loopTimer) clearInterval(loopTimer);
    element.removeEventListener('mouseenter', triggerDecrypt);
    // element.removeEventListener('mouseleave', resetToPlainText);
    element.textContent = text;
  };
}

window.initDecryptedText = initDecryptedText;
