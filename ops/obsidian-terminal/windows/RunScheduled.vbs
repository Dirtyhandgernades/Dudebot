Option Explicit
Dim shell, files, result
Set shell = CreateObject("WScript.Shell")
Set files = CreateObject("Scripting.FileSystemObject")
shell.CurrentDirectory = files.GetParentFolderName(WScript.ScriptFullName)
result = shell.Run(Chr(34) & shell.ExpandEnvironmentStrings("%ComSpec%") & Chr(34) & " /d /c Runner.cmd", 0, True)
WScript.Quit result
