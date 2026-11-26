#ifndef DemoSource
#error Pass /DDemoSource, /DRuntimeRoot, /DHostRoot and /DOutputRoot when compiling.
#endif
[Setup]
AppId=RelayLabD2D25
AppName=Relay Lab
AppVersion=2.5.1
VersionInfoVersion=2.5.1.1
AppPublisher=Relay Lab
DefaultDirName={localappdata}\Programs\Relay Lab 2.5
DefaultGroupName=Relay Lab 2.5
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern
DisableProgramGroupPage=yes
Compression=lzma2/fast
SolidCompression=yes
OutputDir={#OutputRoot}
OutputBaseFilename=Cai_dat_Relay_Lab_2_5_Windows_x64
SetupIconFile={#DemoSource}\desktop\relaylab.ico
UninstallDisplayIcon={app}\RelayLab.exe
UninstallDisplayName=Relay Lab 2.5
SetupLogging=yes
[Files]
Source: "{#DemoSource}\*"; DestDir: "{app}\Demo"; Excludes: "wheels\*,.venv\*,.runtime\*,.luu_phien\*,__pycache__\*,*.pyc"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#RuntimeRoot}\*"; DestDir: "{app}\Demo\.venv\Scripts"; Excludes: "__pycache__\*,*.pyc"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#HostRoot}\RelayLab.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#HostRoot}\*.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#HostRoot}\LICENSE.txt"; DestDir: "{app}\licenses\WebView2"; Flags: ignoreversion
Source: "{#HostRoot}\NOTICE.txt"; DestDir: "{app}\licenses\WebView2"; Flags: ignoreversion
[Icons]
Name: "{userdesktop}\Relay Lab"; Filename: "{app}\RelayLab.exe"; WorkingDir: "{app}"; AppUserModelID: "RelayLab.Desktop"
Name: "{group}\Relay Lab - Đo trên thiết bị"; Filename: "{app}\RelayLab.exe"; WorkingDir: "{app}"; AppUserModelID: "RelayLab.Desktop"
Name: "{group}\Relay Lab - Tập trên laptop"; Filename: "{app}\RelayLab.exe"; Parameters: "--practice"; WorkingDir: "{app}"; AppUserModelID: "RelayLab.Desktop.Practice"
Name: "{group}\Hướng dẫn và kịch bản demo"; Filename: "{app}\Demo\Huong_dan_Relay_Lab_2_5_va_demo.pdf"
[Run]
Filename: "{app}\RelayLab.exe"; WorkingDir: "{app}"; Description: "Mở Relay Lab"; Flags: nowait postinstall skipifsilent

