; Script tạo installer cho myapp.exe

[Setup]
AppName=My GPP-3323 Controller
AppVersion=1.0.3
DefaultDirName={pf}\MyGPPController
DefaultGroupName=My GPP-3323 Controller
OutputBaseFilename=MyGPPController_Installer
OutputDir=D:\DuyTruong\Git\App_control_powersupply\Output
Compression=lzma
SolidCompression=yes
SetupIconFile=D:\DuyTruong\Git\App_control_powersupply\assets\myicon.ico

[Files]
; copy driver vào thư mục tạm thời của installer
Source: "D:\DuyTruong\Git\App_control_powersupply\GPP_1_0_0_3_driverSetup\driverSetup.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall
; copy app chính
Source: "D:\DuyTruong\Git\App_control_powersupply\dist\main.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\My GPP-3323 Controller"; Filename: "{app}\main.exe"
Name: "{commondesktop}\My GPP-3323 Controller"; Filename: "{app}\main.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Tạo biểu tượng trên Desktop"; GroupDescription: "Chọn các tác vụ bổ sung"; Flags: unchecked

[Run]
; Chạy cài đặt driver trước
Filename: "{tmp}\driverSetup.exe"; Description: "Cài driver USB GPP-3323"; Flags: waituntilterminated runhidden
; Sau khi driver cài xong, cài app xong thì hỏi có chạy luôn app không
Filename: "{app}\main.exe"; Description: "Chạy chương trình sau khi cài đặt"; Flags: nowait postinstall skipifsilent
