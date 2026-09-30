; RKNHS — установщик Windows (Inno Setup 6)
; Сборка: python installer/build_installer.py

#define AppName "RKNHS"
#define AppPublisher "Sazzero"
#define AppURL "https://github.com/Sazzero"
#define AppExeName "RKNHS.exe"
; Версия передаётся при сборке: ISCC /DAppVersion=... /DAppVersionFile=...
#ifndef AppVersion
  #define AppVersion "21.1.0.0"
#endif
#ifndef AppVersionFile
  #define AppVersionFile "21.1.0.0"
#endif

[Setup]
AppId={{A7B3C9E1-4F2D-4A8B-9C01-SAZZERO2026}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion} (Sazzero)
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=..\dist\installer
OutputBaseFilename=RKNHS_Setup_{#AppVersionFile}
SetupIconFile=..\ico\RKNHS.ico
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName} (модификация Sazzero)
WizardStyle=modern
WizardSizePercent=120,120
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
Compression=lzma2/ultra64
SolidCompression=yes
MinVersion=10.0
ShowLanguageDialog=no
LicenseFile=
InfoBeforeFile=
ChangesAssociations=no

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[CustomMessages]
russian.WelcomeLabel2=Мастер установит %1 на ваш компьютер.%n%n%1 — собственная модификация обхода блокировок РКН от Sazzero. В комплект входят пресеты DPI, списки доменов и VPN Split (файл AmneziaWG .conf вы указываете сами после установки).%n%nРекомендуется закрыть остальные приложения перед продолжением.
russian.TasksAutostartDescription=Дополнительные параметры:
russian.TasksAutostartLabel=Запускать {#AppName} при входе в Windows (в трее)
russian.TasksDesktopIconDescription=Ярлыки:
russian.TasksDesktopIconLabel=Создать ярлык на рабочем столе
russian.FinishedLabel=Установка %1 завершена. Программа готова к использованию.%n%nПри первом запуске укажите свой .conf AmneziaWG на вкладке VPN Split, если нужен раздельный VPN.

[Tasks]
Name: "desktopicon"; Description: "{cm:TasksDesktopIconLabel}"; GroupDescription: "{cm:TasksDesktopIconDescription}"; Flags: unchecked
Name: "autostart"; Description: "{cm:TasksAutostartLabel}"; GroupDescription: "{cm:TasksAutostartDescription}"; Flags: unchecked

[Dirs]
Name: "{app}\logs"; Permissions: users-modify
Name: "{app}\tmp"; Permissions: users-modify
Name: "{app}\settings\vpn"; Permissions: users-modify

[Files]
; GUI (PyInstaller onedir)
Source: "..\dist\installer_stage\RKNHS.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\installer_stage\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

; Движок DPI и данные
Source: "..\dist\installer_stage\bin\*"; DestDir: "{app}\bin"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\dist\installer_stage\exe\*"; DestDir: "{app}\exe"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\dist\installer_stage\lua\*"; DestDir: "{app}\lua"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\dist\installer_stage\lists\*"; DestDir: "{app}\lists"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\dist\installer_stage\presets\*"; DestDir: "{app}\presets"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\dist\installer_stage\windivert.filter\*"; DestDir: "{app}\windivert.filter"; Flags: ignoreversion recursesubdirs createallsubdirs

; Профили, каталоги, темы
Source: "..\dist\installer_stage\profile\*"; DestDir: "{app}\profile"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\dist\installer_stage\json\*"; DestDir: "{app}\json"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\dist\installer_stage\themes\*"; DestDir: "{app}\themes"; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist
Source: "..\dist\installer_stage\sos\*"; DestDir: "{app}\sos"; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist
Source: "..\dist\installer_stage\ico\*"; DestDir: "{app}\ico"; Flags: ignoreversion recursesubdirs createallsubdirs

; Настройки по умолчанию (без VPN .conf и личных данных)
Source: "..\dist\installer_stage\settings\settings.json"; DestDir: "{app}\settings"; Flags: onlyifdoesntexist ignoreversion
Source: "..\dist\installer_stage\config\config.json"; DestDir: "{app}\config"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"; Comment: "RKNHS — модификация Sazzero"
Name: "{group}\Удалить {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon
Name: "{userstartup}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Parameters: "--tray"; WorkingDir: "{app}"; Tasks: autostart

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Запустить {#AppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\tmp"

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssInstall then
  begin
    { При обновлении не перезаписываем settings.json — флаг onlyifdoesntexist в [Files] }
  end;
end;

function InitializeSetup(): Boolean;
begin
  Result := True;
end;
