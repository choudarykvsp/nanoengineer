; Script generated by the HM NIS Edit Script Wizard.

; HM NIS Edit Wizard helper defines
!define PRODUCT_VERSION "3.3.2+HDF5_p2"
!define PRODUCT_NAME "GROMACS"
!define PRODUCT_PUBLISHER "Nanorex, Inc"
!define PRODUCT_WEB_SITE "http://www.nanorex.com"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\${PRODUCT_NAME}\${PRODUCT_VERSION}"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"

; MUI 1.67 compatible ------
!include "MUI.nsh"

; MUI Settings
!define MUI_ABORTWARNING
!define MUI_ICON "install.ico"
!define MUI_UNICON "uninstall.ico"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "install-header.bmp"
!define MUI_HEADERIMAGE_UNBITMAP "install-header.bmp"
!define MUI_WELCOMEFINISHPAGE_BITMAP "wizard-sidebar.bmp"
!define MUI_UNWELCOMEFINISHPAGE_BITMAP "wizard-sidebar.bmp"

; Welcome page
!insertmacro MUI_PAGE_WELCOME
; License page
!insertmacro MUI_PAGE_LICENSE ".\License.txt"
; Components page
!insertmacro MUI_PAGE_COMPONENTS
; Directory page
!define MUI_DIRECTORYPAGE_TEXT_DESTINATION "Install Folder"
!insertmacro MUI_PAGE_DIRECTORY
; Instfiles page
!insertmacro MUI_PAGE_INSTFILES
; Finish page
!define MUI_FINISHPAGE_SHOWREADME ".\ReadMe.html"
!insertmacro MUI_PAGE_FINISH

; Uninstaller pages
!insertmacro MUI_UNPAGE_INSTFILES

; Language files
!insertmacro MUI_LANGUAGE "English"

; MUI end ------

Name "${PRODUCT_NAME}-${PRODUCT_VERSION}"
OutFile "GROMACS_${PRODUCT_VERSION}.exe"
InstallDir "c:\GROMACS_${PRODUCT_VERSION}\"
InstallDirRegKey HKLM "${PRODUCT_DIR_REGKEY}" ""
ShowInstDetails show
ShowUnInstDetails show

SectionGroup /e "GROMACS"
Section "GROMACS+HDF5 (Required)" SEC_GMX_BASE
  SetOutPath "$INSTDIR"
  SetOverwrite try
  File "..\ReadMe.html"
  File ".\License.txt"
  SetOutPath "$INSTDIR\bin"
  SetOverwrite try
  File ".\dist\bin\*"
SectionEnd
Section /o "Headers & Libraries" SEC_GMX_LIBHDR
  SetOutPath "$INSTDIR\include\gromacs"
  File ".\dist\include\gromacs\*"
  SetOutPath "$INSTDIR\include\gromacs\types"
  File ".\dist\include\gromacs\types\*"
  SetOutPath "$INSTDIR\include\gromacs"
  File ".\dist\include\gromacs\*"
  SetOutPath "$INSTDIR\lib"
  File ".\dist\lib\*"
SectionEnd
Section "Documentation" SEC_GMX_DOC
  SetOverwrite try
  SetOutPath "$INSTDIR\share\gromacs\html"
  File ".\dist\share\gromacs\html\*"
  SetOutPath "$INSTDIR\share\gromacs\html\images"
  File ".\dist\share\gromacs\html\images\*"
  SetOutPath "$INSTDIR\share\gromacs\html\online"
  File ".\dist\share\gromacs\html\online\*"
  SetOutPath "$INSTDIR\share\gromacs\template"
  File ".\dist\share\gromacs\template\*"
  SetOutPath "$INSTDIR\share\gromacs\top"
  File ".\dist\share\gromacs\top\*"
SectionEnd
Section "Tutorials" SEC_GMX_TUTOR
  SetOverwrite try
  SetOutPath "$INSTDIR\share\gromacs\tutor"
  File ".\dist\share\gromacs\tutor\*"
  SetOutPath "$INSTDIR\share\gromacs\tutor\gmxdemo"
  File ".\dist\share\gromacs\tutor\gmxdemo\*"
  SetOutPath "$INSTDIR\share\gromacs\tutor\methanol"
  File ".\dist\share\gromacs\tutor\methanol\*"
  SetOutPath "$INSTDIR\share\gromacs\tutor\mixed"
  File ".\dist\share\gromacs\tutor\mixed\*"
  SetOutPath "$INSTDIR\share\gromacs\tutor\nmr1"
  File ".\dist\share\gromacs\tutor\nmr1\*"
  SetOutPath "$INSTDIR\share\gromacs\tutor\nmr2"
  File ".\dist\share\gromacs\tutor\nmr2\*"
  SetOutPath "$INSTDIR\share\gromacs\tutor\speptide"
  File ".\dist\share\gromacs\tutor\speptide\*"
  SetOutPath "$INSTDIR\share\gromacs\tutor\water"
  File ".\dist\share\gromacs\tutor\water\*"
SectionEnd
Section /o "Source" SEC_GMX_SRC
  SetOverwrite try
  SetOutPath "$INSTDIR\source"
  file /r ".\dist\src\gromacs-3.3.2\*"
SectionEnd
SectionGroupEnd

SectionGroup /e "MCPP"
Section "MCPP (Required)" SEC_MCPP
  SetOutPath "$INSTDIR\MCPP\bin"
  File ".\mcpp\bin\mcpp.exe"
  SetOutPath "$INSTDIR\MCPP"
  File ".\mcpp\LICENSE"
  File ".\mcpp\mcpp-manual-jp.html"
  File ".\mcpp\mcpp-manual.html"
  File ".\mcpp\NEWS"
  File ".\mcpp\README"
SectionEnd
Section /o "Source" SEC_MCPP_SRC
  SetOutPath "$INSTDIR\MCPP\source"
  File /r ".\mcpp\source\*"
SectionEnd
SectionGroupEnd

Section -AdditionalIcons
  SetOutPath $INSTDIR
  CreateDirectory "$SMPROGRAMS\Nanorex\GROMACS_${PRODUCT_VERSION}"
  CreateShortCut "$SMPROGRAMS\Nanorex\GROMACS_${PRODUCT_VERSION}\Uninstall.lnk" "$INSTDIR\uninst.exe"
SectionEnd

Section -Post
  WriteUninstaller "$INSTDIR\uninst.exe"
  WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\bin\mdrun.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "$(^Name)"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninst.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\bin\mdrun.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
SectionEnd

; Section descriptions
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC_GMX_BASE} "Base GROMACS install with experimental HDF5 support (will not affect regular GMX performance.)"
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC_GMX_DOC} "GROMACS documentation."
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC_GMX_TUTOR} "GROMACS tutorials."
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC_GMX_SRC} "Source code for GROMACS patched with the experimental HDF5_SimResults file format."
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC_GMX_LIBHDR} "Headers and libraries for GROMACS development."
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC_MCPP} "A free, open-source C pre-processor for use with GROMACS."
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC_MCPP_SRC} "Source code for MCPP"
!insertmacro MUI_FUNCTION_DESCRIPTION_END


Function un.onUninstSuccess
  HideWindow
  MessageBox MB_ICONINFORMATION|MB_OK "$(^Name) was successfully removed from your computer."
FunctionEnd

Function un.onInit
  MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 "Are you sure you want to completely remove $(^Name) and all of its components?" IDYES +2
  Abort
FunctionEnd

Section Uninstall
  Delete "$INSTDIR\uninst.exe"
  Delete "$INSTDIR\Readme.html"
  Delete "$INSTDIR\License.txt"
  Delete "$INSTDIR\MCCP\README"
  Delete "$INSTDIR\MCCP\NEWS"
  Delete "$INSTDIR\MCCP\mcpp-manual.html"
  Delete "$INSTDIR\MCCP\mcpp-manual-jp.html"
  Delete "$INSTDIR\MCCP\LICENSE"
  Delete "$INSTDIR\MCCP\bin\mcpp.exe"
  Delete "$INSTDIR\lib\*"
  Delete "$INSTDIR\include\gromacs\*"
  Delete "$INSTDIR\include\gromacs\types\*"
  Delete "$INSTDIR\share\gromacs\html\images\*"
  Delete "$INSTDIR\share\gromacs\html\online\*"
  Delete "$INSTDIR\share\gromacs\html\*"
  Delete "$INSTDIR\share\gromacs\template\*"
  Delete "$INSTDIR\share\gromacs\top\*"
  Delete "$INSTDIR\share\gromacs\tutor\methanol\*"
  Delete "$INSTDIR\share\gromacs\tutor\mixed\*"
  Delete "$INSTDIR\share\gromacs\tutor\nmr1\*"
  Delete "$INSTDIR\share\gromacs\tutor\nmr2\*"
  Delete "$INSTDIR\share\gromacs\tutor\speptide\*"
  Delete "$INSTDIR\share\gromacs\tutor\water\*"
  Delete "$INSTDIR\share\gromacs\tutor\gmxdemo\*"
  Delete "$INSTDIR\share\gromacs\tutor\*"
  Delete "$INSTDIR\share\*"
  Delete "$INSTDIR\bin\*"

  Delete "$SMPROGRAMS\Nanorex\GROMACS_${PRODUCT_VERSION}\Uninstall.lnk"

  RMDir "$SMPROGRAMS\Nanorex\GROMACS_${PRODUCT_VERSION}"
  RMDir "$SMPROGRAMS\Nanorex"
  RMDir "$INSTDIR\MCPP\bin"
  RMDir /r "$INSTDIR\MCPP"
  RMDir "$INSTDIR\lib"
  RMDir "$INSTDIR\include\gromacs\types"
  RMDir "$INSTDIR\include\gromacs"
  RMDir "$INSTDIR\include\"
  RMDir "$INSTDIR\share\gromacs\html\images"
  RMDir "$INSTDIR\share\gromacs\html\online"
  RMDir "$INSTDIR\share\gromacs\html"
  RMDir "$INSTDIR\share\gromacs\template"
  RMDir "$INSTDIR\share\gromacs\top"
  RMDir "$INSTDIR\share\gromacs\tutor\methanol"
  RMDir "$INSTDIR\share\gromacs\tutor\mixed"
  RMDir "$INSTDIR\share\gromacs\tutor\nmr1"
  RMDir "$INSTDIR\share\gromacs\tutor\nmr2"
  RMDir "$INSTDIR\share\gromacs\tutor\speptide"
  RMDir "$INSTDIR\share\gromacs\tutor\water"
  RMDir "$INSTDIR\share\gromacs\tutor\gmxdemo"
  RMDir "$INSTDIR\share\gromacs\tutor"
  RMDir "$INSTDIR\share\gromacs"
  RMDir "$INSTDIR\share"
  RMDir "$INSTDIR\bin"
  RMDir /r "$INSTDIR\source"
  RMDir "$INSTDIR"

  DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
  DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"
  SetAutoClose true
SectionEnd
