; Inno Setup recipe for the Windows installer, built by .github/workflows/windows.yml after PyInstaller.
; It installs the app, OBS's virtual camera module (so OBS Studio itself isn't needed), and optionally
; downloads VB-CABLE from vb-audio.com: VB-Audio's terms don't allow bundling it.
#define AppVersion GetEnv("APP_VERSION")
#define CableUrl "https://download.vb-audio.com/Download_CABLE/VBCABLE_Driver_Pack45.zip"
; OBS's DirectShow virtual camera, as registered by OBS's own installer.
#define CameraClsid "CLSID\{A3FCE0F5-3493-419F-958A-ABA1250EC20B}\InprocServer32"

[Setup]
AppId={{E47D0CD0-B482-458D-904E-8E06AE09CE4A}
AppName=Redbarn Studio
AppVersion={#AppVersion}
AppPublisher=Redbarn Christian Co.
AppPublisherURL=https://github.com/GoochGrenade/redbarn-studio
AppSupportURL=https://github.com/GoochGrenade/redbarn-studio/issues
AppCopyright=Copyright (C) 2026 Redbarn Christian Co.
DefaultDirName={autopf}\Redbarn Studio
DisableProgramGroupPage=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
LicenseFile=..\LICENSE
OutputDir=..\installer
OutputBaseFilename=Redbarn-Studio-Setup
SetupIconFile=..\redbarn-studio.ico
UninstallDisplayIcon={app}\Redbarn Studio.exe
UninstallDisplayName=Redbarn Studio
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes

[Tasks]
Name: desktopicon; Description: "Create a desktop shortcut"; Flags: unchecked
Name: vbcable; Description: "Install the VB-CABLE virtual mic (downloaded from vb-audio.com; donationware by VB-Audio)"; Check: not CableInstalled

[Files]
Source: "..\dist\Redbarn Studio\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion
Source: "..\virtualcam\*"; DestDir: "{app}\virtualcam"; Flags: recursesubdirs ignoreversion; Check: NeedCamera

[Icons]
Name: "{autoprograms}\Redbarn Studio"; Filename: "{app}\Redbarn Studio.exe"
Name: "{autodesktop}\Redbarn Studio"; Filename: "{app}\Redbarn Studio.exe"; Tasks: desktopicon

[Run]
Filename: "{sys}\regsvr32.exe"; Parameters: "/s ""{app}\virtualcam\obs-virtualcam-module64.dll"""; Flags: runhidden; Check: NeedCamera
Filename: "{syswow64}\regsvr32.exe"; Parameters: "/s ""{app}\virtualcam\obs-virtualcam-module32.dll"""; Flags: runhidden; Check: NeedCamera
Filename: "{app}\Redbarn Studio.exe"; Description: "Open Redbarn Studio"; Flags: nowait postinstall skipifsilent
; An update from inside the app runs silently with /RELAUNCH=1: reopen the app as the user, not as admin.
Filename: "{app}\Redbarn Studio.exe"; Flags: nowait runasoriginaluser; Check: Relaunch

[Registry]
; Start at Login is set by the app itself; only removed here, on uninstall.
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: none; ValueName: "Redbarn Studio"; Flags: uninsdeletevalue dontcreatekey

[Code]
var
  CablePresent, CableTried: Boolean;

function CameraPath(): String;
begin
  if not RegQueryStringValue(HKCR64, '{#CameraClsid}', '', Result) then
    Result := '';
end;

{ Skip our copy when OBS Studio's own virtual camera is already registered and present. }
function NeedCamera(): Boolean;
var
  Path: String;
begin
  Path := CameraPath();
  Result := (Path = '') or not FileExists(Path) or (Pos(Lowercase(ExpandConstant('{app}')), Lowercase(Path)) = 1);
end;

function Relaunch(): Boolean;
begin
  Result := ExpandConstant('{param:relaunch|0}') = '1';
end;

function CableInstalled(): Boolean;
begin
  Result := CablePresent;
end;

function InitializeSetup(): Boolean;
var
  Code: Integer;
begin
  { Checked once: task conditions are evaluated many times, and this takes a second. }
  CablePresent := Exec('powershell.exe', '-NoProfile -Command "if (Get-PnpDevice -FriendlyName ''*VB-Audio Virtual Cable*'' -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }"',
                       '', SW_HIDE, ewWaitUntilTerminated, Code) and (Code = 0);
  Result := True;
end;

procedure InstallCable();
var
  Zip, Folder, Params: String;
  Code: Integer;
begin
  Zip := ExpandConstant('{tmp}\vbcable.zip');
  Folder := ExpandConstant('{tmp}\vbcable');
  try
    DownloadTemporaryFile('{#CableUrl}', 'vbcable.zip', '', nil);
    Exec('powershell.exe', '-NoProfile -Command "Expand-Archive -Force ''' + Zip + ''' ''' + Folder + '''"', '', SW_HIDE, ewWaitUntilTerminated, Code);
    { VB's own window, so the user sees VB-Audio's terms; silent installs (the build server) skip it. }
    if WizardSilent() then Params := '-i -h' else Params := '';
    if not Exec(Folder + '\VBCABLE_Setup_x64.exe', Params, Folder, SW_SHOW, ewWaitUntilTerminated, Code) then
      RaiseException('VBCABLE_Setup_x64.exe did not start');
    CableTried := True;
  except
    Log('VB-CABLE install failed: ' + GetExceptionMessage());
    SuppressibleMsgBox('VB-CABLE couldn''t be downloaded, so the virtual mic isn''t installed yet.' + #13#10 +
                       'Open Setup & Help in Redbarn Studio for the download link.', mbInformation, MB_OK, IDOK);
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if (CurStep = ssPostInstall) and WizardIsTaskSelected('vbcable') then
    InstallCable();
end;

function NeedRestart(): Boolean;
begin
  Result := CableTried;  { Windows only shows a new audio driver after a restart }
end;

{ Unregister the camera only if it's still ours: OBS Studio installed later would have taken it over. }
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  Code: Integer;
begin
  if (CurUninstallStep = usUninstall) and (CameraPath() <> '') and
     (Pos(Lowercase(ExpandConstant('{app}\virtualcam')), Lowercase(CameraPath())) = 1) then begin
    Exec(ExpandConstant('{sys}\regsvr32.exe'), '/u /s "' + ExpandConstant('{app}\virtualcam\obs-virtualcam-module64.dll') + '"', '', SW_HIDE, ewWaitUntilTerminated, Code);
    Exec(ExpandConstant('{syswow64}\regsvr32.exe'), '/u /s "' + ExpandConstant('{app}\virtualcam\obs-virtualcam-module32.dll') + '"', '', SW_HIDE, ewWaitUntilTerminated, Code);
  end;
end;
