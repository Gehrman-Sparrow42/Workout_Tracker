Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "D:\tools\workout_tracker"
WshShell.Run "pythonw main.py", 0, False
