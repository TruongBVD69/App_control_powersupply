; Script tạo installer cho myapp.exe

[Setup]
AppName=My GPP-3323 Controller
AppVersion=1.0
DefaultDirName={pf}\MyGPPController
DefaultGroupName=My GPP-3323 Controller
OutputBaseFilename=MyGPPController_Installer
Compression=lzma
SolidCompression=yes
SetupIconFile=C:\Users\BuiVuDuyTruong\Desktop\Code_control_pw_supplie\sources\myicon.ico

[Files]
; copy driver vào thư mục tạm thời của installer
Source: "C:\Users\BuiVuDuyTruong\Desktop\Code_control_pw_supplie\sources\driver_gpp\driverSetup.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall
; copy app chính
Source: "C:\Users\BuiVuDuyTruong\Desktop\Code_control_pw_supplie\sources\dist\gui_temp.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\My GPP-3323 Controller"; Filename: "{app}\gui_temp.exe"
Name: "{commondesktop}\My GPP-3323 Controller"; Filename: "{app}\gui_temp.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Tạo biểu tượng trên Desktop"; GroupDescription: "Chọn các tác vụ bổ sung"; Flags: unchecked

[Run]
; Chạy cài đặt driver trước
Filename: "{tmp}\driverSetup.exe"; Description: "Cài driver USB GPP-3323"; Flags: waituntilterminated runhidden
; Sau khi driver cài xong, cài app xong thì hỏi có chạy luôn app không
Filename: "{app}\gui_temp.exe"; Description: "Chạy chương trình sau khi cài đặt"; Flags: nowait postinstall skipifsilent
