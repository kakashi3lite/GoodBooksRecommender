# Copilot Continue Button Clicker
# This script monitors for and clicks the "Continue" button in GitHub Copilot chat

# Script configuration
$checkIntervalSeconds = 1
$maxRetries = 3
$memoryThresholdMB = 15
$targetButtonText = "Continue"
$vsCodeProcessName = "Code"
$logFile = "$PSScriptRoot\copilot-clicker.log"

# Required assemblies
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# Statistics
$clickCount = 0
$startTime = Get-Date

# Log startup
"[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Copilot Continue Button Clicker started" | Out-File -FilePath $logFile -Append

# Check if VS Code is running
function Test-VSCodeRunning {
    return Get-Process -Name $vsCodeProcessName -ErrorAction SilentlyContinue
}

# Get VS Code memory usage
function Get-VSCodeMemoryUsage {
    $process = Get-Process -Name $vsCodeProcessName -ErrorAction SilentlyContinue
    if ($process) {
        return [math]::Round($process.WorkingSet64 / 1MB, 2)
    }
    return 0
}

# Search for pixels with the GitHub button blue color
function Find-ContinueButton {
    $screenBounds = [Windows.Forms.Screen]::PrimaryScreen.Bounds
    $primaryColor = [System.Drawing.Color]::FromArgb(0, 122, 204)  # GitHub button blue
    
    # Create a screenshot to analyze
    $bitmap = New-Object System.Drawing.Bitmap $screenBounds.Width, $screenBounds.Height
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.CopyFromScreen($screenBounds.Location, [System.Drawing.Point]::Empty, $screenBounds.Size)
    
    # Areas to search in (bottom of chat panel and middle of screen)
    $areas = @(
        # Bottom area where buttons often appear
        @{
            X1 = $screenBounds.Width / 2 - 200
            Y1 = $screenBounds.Height - 300
            X2 = $screenBounds.Width / 2 + 200
            Y2 = $screenBounds.Height - 100
        },
        # Middle area for inline buttons
        @{
            X1 = $screenBounds.Width / 2 - 300
            Y1 = $screenBounds.Height / 2 - 200
            X2 = $screenBounds.Width / 2 + 300
            Y2 = $screenBounds.Height / 2 + 200
        }
    )
    
    # Search each area
    foreach ($area in $areas) {
        for ($x = $area.X1; $x -lt $area.X2; $x += 10) {
            for ($y = $area.Y1; $y -lt $area.Y2; $y += 10) {
                $pixelColor = $bitmap.GetPixel($x, $y)
                # Check if color is close to GitHub blue
                if ([Math]::Abs($pixelColor.R - $primaryColor.R) -lt 10 -and
                    [Math]::Abs($pixelColor.G - $primaryColor.G) -lt 10 -and
                    [Math]::Abs($pixelColor.B - $primaryColor.B) -lt 10) {
                    
                    # Found a potential button, dispose graphics and bitmap
                    $graphics.Dispose()
                    $bitmap.Dispose()
                    
                    # Return coordinates
                    return @{X = $x; Y = $y }
                }
            }
        }
    }
    
    # Clean up
    $graphics.Dispose()
    $bitmap.Dispose()
    return $null
}

# Click at specified coordinates
function Invoke-Click {
    param (
        [Parameter(Mandatory = $true)]
        [hashtable] $Coordinates
    )
    
    $cursor = [System.Windows.Forms.Cursor]::Position
    
    # Save current position
    $originalX = $cursor.X
    $originalY = $cursor.Y
    
    # Move to target and click
    [System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point($Coordinates.X, $Coordinates.Y)
    Start-Sleep -Milliseconds 50
    
    # Perform click
    $signature = @'
    [DllImport("user32.dll",CharSet=CharSet.Auto, CallingConvention=CallingConvention.StdCall)]
    public static extern void mouse_event(uint dwFlags, uint dx, uint dy, uint cButtons, uint dwExtraInfo);
'@
    $mouseEvent = Add-Type -MemberDefinition $signature -Name "MouseEvent" -Namespace "Win32" -PassThru
    $mouseEvent::mouse_event(0x00000002, 0, 0, 0, 0) # Left mouse button down
    $mouseEvent::mouse_event(0x00000004, 0, 0, 0, 0) # Left mouse button up
    
    # Move back to original position
    Start-Sleep -Milliseconds 50
    [System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point($originalX, $originalY)
    
    return $true
}

# Main monitoring loop
try {
    while ($true) {
        # Check if VS Code is running
        if (-not (Test-VSCodeRunning)) {
            Start-Sleep -Seconds $checkIntervalSeconds
            continue
        }
        
        # Check memory usage
        $memoryUsage = Get-VSCodeMemoryUsage
        if ($memoryUsage -gt $memoryThresholdMB) {
            "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] High memory usage: $memoryUsage MB. Skipping scan." | Out-File -FilePath $logFile -Append
            Start-Sleep -Seconds $checkIntervalSeconds
            continue
        }
        
        # Find the Continue button
        $buttonCoordinates = Find-ContinueButton
        if ($buttonCoordinates) {
            # Click the button
            $clickResult = Invoke-Click -Coordinates $buttonCoordinates
            if ($clickResult) {
                $clickCount++
                "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Continue button clicked successfully ($clickCount total)" | Out-File -FilePath $logFile -Append
            }
        }
        
        # Wait before next scan
        Start-Sleep -Seconds $checkIntervalSeconds
    }
}
finally {
    # Log script end
    $runTime = ((Get-Date) - $startTime).TotalMinutes
    "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Script exiting. Runtime: $($runTime.ToString('0.00')) minutes. Buttons clicked: $clickCount" | Out-File -FilePath $logFile -Append
}
