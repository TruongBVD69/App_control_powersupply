; Script tạo installer cho My GPP-3323 Controller
; #define ProjectDir ExtractFileDir(__FILE__) + "\"
#define MyAppVersion "2.0.3"
#define MyAppName "My GPP-3323 Controller"

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={pf}\MyGPPController
DefaultGroupName=My GPP-3323 Controller
OutputBaseFilename=MyGPPController_Installer
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
Name: "{group}\My GPP-3323 Controller"; Filename: "{app}\main.exe"
Name: "{commondesktop}\My GPP-3323 Controller"; Filename: "{app}\main.exe"; Tasks: desktopicon

Name: "{group}\My GPP-3323 Voice App"; Filename: "{app}\voice_app.exe"
Name: "{commondesktop}\My GPP-3323 Voice App"; Filename: "{app}\voice_app.exe"; Tasks: voice_desktopicon

[Tasks]
Name: "desktopicon"; Description: "Tạo biểu tượng trên Desktop"; GroupDescription: "Chọn các tác vụ bổ sung"
Name: "voice_desktopicon"; Description: "Tạo biểu tượng trên Desktop cho Voice App"; GroupDescription: "Chọn các tác vụ bổ sung"

[Run]
; Chạy cài đặt driver trước
Filename: "{tmp}\driverSetup.exe"; Description: "Cài driver USB GPP-3323"; Flags: waituntilterminated runhidden
; Sau khi driver cài xong, hỏi có chạy luôn app không
Filename: "{app}\main.exe"; Description: "Chạy chương trình sau khi cài đặt"; Flags: nowait postinstall skipifsilent
; Chạy tiếp voice_app.exe cũng hỏi có chạy luôn app không
Filename: "{app}\voice_app.exe"; Description: "Chạy ứng dụng Voice sau khi cài đặt"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

