// This file can be loaded by VS Code when enabled through settings.json
// It injects the feedback overlay for Copilot Continue Button clicks

(function() {
  // Only run in GitHub Copilot Chat views
  if (document.querySelector('.github-copilot-chat-view-container')) {
    // Dynamically load our script
    const script = document.createElement('script');
    script.src = 'vscode-file://vscode-app/c:/Users/Swanand/CascadeProjects/GoodBooksRecommender/.vscode/scripts/copilot-feedback-overlay.js';
    document.head.appendChild(script);
    
    // Watch for continue button appearances
    const observer = new MutationObserver((mutations) => {
      for (const mutation of mutations) {
        if (mutation.type === 'childList' && mutation.addedNodes.length) {
          // Look for buttons that might be the continue button
          const continueButton = document.querySelector('button:not([data-observed]):contains("Continue")');
          if (continueButton) {
            continueButton.setAttribute('data-observed', 'true');
            continueButton.addEventListener('click', () => {
              // Send message to our overlay
              window.postMessage({ type: 'copilot-button-clicked' }, '*');
            });
          }
        }
      }
    });
    
    observer.observe(document.body, { 
      childList: true, 
      subtree: true 
    });
    
    console.log('Copilot Continue Button Clicker observer initialized');
  }
})();
