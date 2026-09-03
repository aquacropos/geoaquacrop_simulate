' ============================================================================
'  keep_awake.vbs
'
'  Keeps Windows awake by sending a harmless keystroke every 4 minutes.
'  VBScript is not affected by PowerShell execution policy.
'
'  Run in its own Command Prompt window:
'      cscript keep_awake.vbs
'
'  Stop with Ctrl+C or by closing the window.
'
'  F15 is used because it is a real key code that resets the idle timer but is
'  not mapped to anything on a normal keyboard, so it cannot type into or
'  disturb whatever window happens to be focused. It does still go to the active
'  window, so avoid leaving a text editor focused just in case.
' ============================================================================

Dim shell, mins
Set shell = WScript.CreateObject("WScript.Shell")
mins = 0

WScript.Echo "Keeping this PC awake. Leave this window open. Ctrl+C to stop."
WScript.Echo "Started " & Now

Do While True
    WScript.Sleep 240000          ' 4 minutes
    shell.SendKeys "{F15}"
    mins = mins + 4
    WScript.Echo "  still awake, " & mins & " min elapsed (" & Time & ")"
Loop
