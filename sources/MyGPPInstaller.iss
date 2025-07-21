; Script tạo installer cho My GPP-3323 Controller
#define MyAppVersion "1.0.3"
#define MyAppName "My GPP-3323 Controller"
#define MyOutputDir "D:\DuyTruong\Git\App_control_powersupply\Output"

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={pf}\MyGPPController
DefaultGroupName=My GPP-3323 Controller
OutputBaseFilename=MyGPPController_Installer
OutputDir={#MyOutputDir}
Compression=lzma
SolidCompression=yes
SetupIconFile=D:\DuyTruong\Git\App_control_powersupply\assets\myicon.ico

[Files]
; copy driver vào thư mục tạm thời của installer
Source: "D:\DuyTruong\Git\App_control_powersupply\GPP_1_0_0_3_driverSetup\driverSetup.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall
; copy app chính (đổi tên file exe nếu cần)
Source: "D:\DuyTruong\Git\App_control_powersupply\dist\main.exe"; DestDir: "{app}"; Flags: ignoreversion
; copy file version.txt vào thư mục cài đặt
Source: "D:\DuyTruong\Git\App_control_powersupply\Output\version.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\My GPP-3323 Controller"; Filename: "{app}\main.exe"
Name: "{commondesktop}\My GPP-3323 Controller"; Filename: "{app}\main.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Tạo biểu tượng trên Desktop"; GroupDescription: "Chọn các tác vụ bổ sung"; Flags: unchecked

[Run]
; Chạy cài đặt driver trước
Filename: "{tmp}\driverSetup.exe"; Description: "Cài driver USB GPP-3323"; Flags: waituntilterminated runhidden
; Sau khi driver cài xong, hỏi có chạy luôn app không
Filename: "{app}\main.exe"; Description: "Chạy chương trình sau khi cài đặt"; Flags: nowait postinstall skipifsilent
