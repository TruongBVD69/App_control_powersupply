; Script tạo installer cho My GPP-3323 Controller
; #define ProjectDir ExtractFileDir(__FILE__) + "\"
#define MyAppVersion "2.1.3"
#define MyAppName "PowerSupply Controller"

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={pf}\PowerSupply Controller
DefaultGroupName=PowerSupply Controller
OutputBaseFilename=PowerSupplyController
OutputDir={#SourcePath}..\Output
Compression=lzma
SolidCompression=yes
SetupIconFile={#SourcePath}..\assets\myicon.ico

[Files]
; copy driver vào thư mục tạm thời của installer
Source: "{#SourcePath}..\GPP_1_0_0_3_driverSetup\driverSetup.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall
; copy app chính (đổi tên file exe nếu cần)
Source: "{#SourcePath}..\dist\main\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; copy file version.txt vào thư mục cài đặt
Source: "{#SourcePath}..\Output\version.txt"; DestDir: "{app}"; Flags: ignoreversion
; copy file app phụ
Source: "{#SourcePath}..\dist\voice_app\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\PowerSupply Controller"; Filename: "{app}\main.exe"
Name: "{commondesktop}\PowerSupply Controller"; Filename: "{app}\main.exe"; Tasks: desktopicon

Name: "{group}\PowerSupply Voice App"; Filename: "{app}\voice_app.exe"
Name: "{commondesktop}\PowerSupply Voice App"; Filename: "{app}\voice_app.exe"; Tasks: voice_desktopicon

[Tasks]
Name: "desktopicon"; Description: "Tạo biểu tượng trên Desktop"; GroupDescription: "Chọn các tác vụ bổ sung"
Name: "voice_desktopicon"; Description: "Tạo biểu tượng trên Desktop cho Voice App"; GroupDescription: "Chọn các tác vụ bổ sung"

[Run]
; Chạy cài đặt driver trước
Filename: "{tmp}\driverSetup.exe"; Description: "Cài driver USB GPP-3323"; Flags: waituntilterminated runhidden
; Sau khi driver cài xong, hỏi có chạy luôn app không
Filename: "{app}\main.exe"; Description: "Chạy chương trình sau khi cài đặt"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

