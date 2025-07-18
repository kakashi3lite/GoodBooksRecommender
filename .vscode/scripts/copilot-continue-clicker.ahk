#NoEnv  ; Recommended for performance and compatibility with future AutoHotkey releases
#Persistent  ; Keep the script running until manually terminated
#SingleInstance Force  ; Replace old instances with new ones
SetBatchLines, -1  ; Never sleep, use minimal CPU
SetWinDelay, 0  ; No delays between window commands
ListLines Off  ; Save memory and CPU by not keeping track of executed lines

; Configuration
global checkIntervalMs := 1000  ; Check every 1 second
global maxRetries := 3  ; Maximum number of retries if clicking fails
global memoryThreshold := 15  ; Threshold in MB to pause scanning if VS Code memory usage is high
global targetButtonText := "Continue"  ; Text to find in the button
global vsCodeTitle := "ahk_exe Code.exe"  ; VS Code process name

; Statistics
global clickCount := 0
global lastFoundTime := 0
global startTime := A_TickCount

; Start the timer loop
SetTimer, CheckForContinueButton, %checkIntervalMs%

; Log startup information
FormatTime, currentTime,, yyyy-MM-dd HH:mm:ss
FileAppend, [%currentTime%] Copilot Continue Button Clicker started`n, %A_ScriptDir%\copilot-clicker.log

; Memory-aware checking function
CheckForContinueButton() {
    ; Skip if VS Code is not active to save resources
    If (!WinExist(vsCodeTitle)) {
        Return
    }
    
    ; Check memory usage of VS Code
    Process, Exist, Code.exe
    If (ErrorLevel) {
        pid := ErrorLevel
        memory := GetProcessMemory(pid)
        
        ; Skip checking if memory usage is too high
        If (memory > memoryThreshold) {
            FileAppend, % "[" . FormatTime(, "yyyy-MM-dd HH:mm:ss") . "] High memory usage: " . memory . " MB. Skipping scan.`n", %A_ScriptDir%\copilot-clicker.log
            Return
        }
    }
    
    ; Look for the GitHub Copilot Chat panel
    If (FindCopilotChatPanel()) {
        ; Look for the Continue button
        continueButtonFound := FindAndClickContinueButton()
        
        ; If found and clicked, log it
        If (continueButtonFound) {
            clickCount += 1
            lastFoundTime := A_TickCount
            FormatTime, currentTime,, yyyy-MM-dd HH:mm:ss
            FileAppend, [%currentTime%] Continue button clicked successfully (%clickCount% total)`n, %A_ScriptDir%\copilot-clicker.log
        }
    }
}

; Find the Copilot Chat panel
FindCopilotChatPanel() {
    ; This is a placeholder - real implementation would search the VS Code DOM
    ; Since AHK can't directly access the DOM, we're using image/pixel detection methods
    
    ; For now, just check if VS Code is active
    IfWinActive, %vsCodeTitle%
    {
        Return True
    }
    Return False
}

; Find and click the Continue button using pixel color and position detection
FindAndClickContinueButton() {
    ; This is where we'd implement UI scanning for the button
    ; Real implementation would use image recognition or pixel color patterns
    
    ; Visual scanning using pixel patterns characteristic of the button
    ; Scan specific regions where the continue button is likely to appear
    
    ; Primary location check (bottom of the chat panel)
    PixelSearch, FoundX, FoundY, A_ScreenWidth/2-200, A_ScreenHeight-300, A_ScreenWidth/2+200, A_ScreenHeight-100, 0x007ACC, 3, Fast
    If (!ErrorLevel) {
        ; Found something that might be the button
        MouseMove, %FoundX%, %FoundY%, 0
        Sleep, 10
        Click
        Return True
    }
    
    ; Secondary location check (inline in the chat)
    PixelSearch, FoundX, FoundY, A_ScreenWidth/2-300, A_ScreenHeight/2-200, A_ScreenWidth/2+300, A_ScreenHeight/2+200, 0x007ACC, 3, Fast
    If (!ErrorLevel) {
        ; Found something that might be the button
        MouseMove, %FoundX%, %FoundY%, 0
        Sleep, 10
        Click
        Return True
    }
    
    Return False
}

; Function to get memory usage of a process
GetProcessMemory(pid) {
    memory := 0
    
    ; Get process memory info using WMI
    for process in ComObjGet("winmgmts:").ExecQuery("SELECT WorkingSetSize FROM Win32_Process WHERE ProcessId = " pid)
        memory := process.WorkingSetSize / 1024 / 1024 ; Convert to MB
        
    Return memory
}

; Exit handler
OnExit, ExitHandler
Return

ExitHandler:
    FormatTime, currentTime,, yyyy-MM-dd HH:mm:ss
    runTime := (A_TickCount - startTime) / 1000 / 60 ; minutes
    FileAppend, [%currentTime%] Script exiting. Runtime: %runTime% minutes. Buttons clicked: %clickCount%`n, %A_ScriptDir%\copilot-clicker.log
ExitApp
