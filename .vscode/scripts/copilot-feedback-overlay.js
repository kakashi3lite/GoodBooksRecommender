/**
 * Copilot Continue Button Feedback Overlay
 * Shows a subtle visual feedback when the continue button is automatically clicked
 */

// Configuration settings
const OVERLAY_DURATION_MS = 500; // How long the overlay shows
const DEFAULT_BRIGHTNESS = 0.5; // Default brightness (0-1)

class CopilotFeedbackOverlay {
  constructor() {
    this.overlay = null;
    this.brightness = localStorage.getItem('copilotOverlayBrightness') || DEFAULT_BRIGHTNESS;
    this.init();
  }

  init() {
    // Create the overlay element
    this.overlay = document.createElement('div');
    this.overlay.id = 'copilot-feedback-overlay';
    this.overlay.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      background-color: rgba(30, 64, 175, ${this.brightness * 0.3});
      pointer-events: none;
      z-index: 99999;
      opacity: 0;
      transition: opacity 0.2s ease-in-out;
      display: none;
    `;

    // Create brightness control
    this.brightnessControl = document.createElement('div');
    this.brightnessControl.id = 'copilot-brightness-control';
    this.brightnessControl.style.cssText = `
      position: fixed;
      bottom: 20px;
      right: 20px;
      background-color: rgba(0, 0, 0, 0.7);
      padding: 10px;
      border-radius: 8px;
      z-index: 100000;
      display: none;
      color: white;
      font-family: system-ui, sans-serif;
      font-size: 12px;
    `;
    
    this.brightnessControl.innerHTML = `
      <div style="margin-bottom: 5px;">Overlay Brightness</div>
      <input type="range" min="0" max="100" value="${this.brightness * 100}" 
       style="width: 100%;" id="copilot-brightness-slider">
    `;

    // Add elements to DOM
    document.body.appendChild(this.overlay);
    document.body.appendChild(this.brightnessControl);

    // Setup event listeners
    this.setupEventListeners();
    
    // Register message listener for the AutoHotKey script to call
    window.addEventListener('message', (event) => {
      if (event.data && event.data.type === 'copilot-button-clicked') {
        this.flash();
      }
    });
  }

  setupEventListeners() {
    // Setup brightness slider
    const slider = document.getElementById('copilot-brightness-slider');
    if (slider) {
      slider.addEventListener('input', (e) => {
        this.brightness = e.target.value / 100;
        localStorage.setItem('copilotOverlayBrightness', this.brightness);
        this.overlay.style.backgroundColor = `rgba(30, 64, 175, ${this.brightness * 0.3})`;
        
        // Flash to show preview
        this.flash();
      });
    }

    // Toggle brightness control with Alt+B
    document.addEventListener('keydown', (e) => {
      if (e.altKey && e.key === 'b') {
        if (this.brightnessControl.style.display === 'none') {
          this.brightnessControl.style.display = 'block';
        } else {
          this.brightnessControl.style.display = 'none';
        }
      }
    });
  }

  flash() {
    if (!this.overlay) return;
    
    // Display and animate the overlay
    this.overlay.style.display = 'block';
    setTimeout(() => {
      this.overlay.style.opacity = '1';
    }, 10);
    
    // Hide after duration
    setTimeout(() => {
      this.overlay.style.opacity = '0';
      setTimeout(() => {
        this.overlay.style.display = 'none';
      }, 200);
    }, OVERLAY_DURATION_MS);
  }
}

// Initialize when DOM is ready
if (document.readyState === 'complete' || document.readyState === 'interactive') {
  new CopilotFeedbackOverlay();
} else {
  document.addEventListener('DOMContentLoaded', () => {
    new CopilotFeedbackOverlay();
  });
}
