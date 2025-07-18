# 🤖 GitHub Copilot Continue Button Clicker

This automation tool automatically clicks the "Continue" button in GitHub Copilot chat interfaces, helping you maintain a fluid coding experience without manual interruptions.

## Features

- **Lightweight & Efficient**: Uses minimal CPU (<1%) and memory (<15MB)
- **Smart Detection**: Identifies and clicks only the GitHub Copilot "Continue" button
- **Visual Feedback**: Optional overlay shows when button is clicked (Alt+B to configure)
- **Memory-Aware**: Pauses when VS Code memory usage is high
- **Easy Controls**: Start/stop from VS Code tasks menu
- **Detailed Logging**: Tracks all actions for troubleshooting

## Setup & Usage

### Quick Start

1. **Option 1 (AutoHotKey)**: Run VS Code task `🤖 Copilot Continue Button Clicker (AHK)`
   - Requires AutoHotKey installed on your system
   - More reliable for pixel-based detection

2. **Option 2 (PowerShell)**: Run VS Code task `🤖 Copilot Continue Button Clicker (PS)`
   - No additional software required
   - Uses PowerShell for automation

### Task Commands

- **Start AutoHotKey Clicker**: `🤖 Copilot Continue Button Clicker (AHK)`
- **Start PowerShell Clicker**: `🤖 Copilot Continue Button Clicker (PS)`
- **Stop Clicker**: `🛑 Stop Copilot Button Clicker`
- **View Logs**: `📊 View Copilot Clicker Log`
- **Configure**: `⚙️ Configure Copilot Button Clicker`

### Visual Feedback (Optional)

- Press `Alt+B` to show brightness control for the feedback overlay
- Adjust the brightness slider to your preference
- Visual feedback appears as a subtle blue flash when a button is clicked

## Customization

### Script Locations

- **AutoHotKey**: `.vscode/scripts/copilot-continue-clicker.ahk`
- **PowerShell**: `.vscode/scripts/copilot-continue-clicker.ps1`
- **Visual Overlay**: `.vscode/scripts/copilot-feedback-overlay.js`

### Configuration Options

Both scripts have configuration variables at the top:

- **Check Interval**: How often to scan for the button (default: 1 second)
- **Memory Threshold**: When to pause scanning (default: 15MB)
- **Button Properties**: What text/colors to look for

## Troubleshooting

1. **No clicks detected**
   - Check logs with the `📊 View Copilot Clicker Log` task
   - Ensure VS Code has focus when the button appears
   - Try adjusting the detection areas in the script

2. **High CPU usage**
   - Increase the check interval in the script
   - Make sure no other automation scripts are running

3. **Incorrect clicks**
   - Adjust the button detection parameters
   - Try the alternative script (AHK or PowerShell)

## Security Note

This tool uses UI automation which may be detected by security software. It only runs when VS Code is active and targets only the "Continue" button within the GitHub Copilot interface.

---

_Created by Superhuman VS Code Extensions Engineer, 2025_
