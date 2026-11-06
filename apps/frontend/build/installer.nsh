; NSIS custom script for Twitch Clipper installer
; Grava a entrada de auto-start no registro (HKCU Run)

!macro customInstall
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "TwitchClipper" "$INSTDIR\Twitch Clipper.exe"
!macroend

!macro customUnInstall
  DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "TwitchClipper"
!macroend
