; OmniLauncher-MC Installer Script
; Customized Inno Setup

#define MyAppName "OmniLauncher-MC"
#define MyAppVersion "0.1.1"
#define MyAppPublisher "OmniNodeCo"
#define MyAppURL "https://github.com/OmniNodeCo/OmniLauncher-MC"
#define MyAppExeName "OmniLauncher-MC.exe"
#define AppId a41a5585-b9c3-4d95-b6f5-0266cf90d6de

[Setup]
AppId={{YOUR-UNIQUE-GUID-HERE}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=installer-output
OutputBaseFilename=OmniLauncher-MC-Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
WizardSizePercent=120,120
DisableWelcomePage=no

; Visual customization
WindowVisible=yes
WindowShowCaption=yes
WindowResizable=no

; Colors
WizardImageBackColor=$1a1a2e
SetupIconFile=assets\icon.ico
WizardImageFile=assets\installer-banner.bmp
WizardSmallImageFile=assets\installer-logo.bmp

; Minimum OS
MinVersion=10.0

; Privileges
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; Uninstaller
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Messages]
WelcomeLabel1=Welcome to {#MyAppName}
WelcomeLabel2=This will install {#MyAppName} {#MyAppVersion} on your computer.%n%n{#MyAppName} is a custom Minecraft launcher by {#MyAppPublisher}.%n%nClick Next to continue.
FinishedHeadingLabel=Installation Complete!
FinishedLabel={#MyAppName} has been installed successfully.%n%nClick Finish to launch the application.

[Tasks]
Name: "desktopicon"; Description: "Create a Desktop shortcut"; GroupDescription: "Shortcuts:"; Flags: checkedonce
Name: "startmenu"; Description: "Create a Start Menu shortcut"; GroupDescription: "Shortcuts:"; Flags: checkedonce

[Files]
Source: "dist\OmniLauncher-MC\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: startmenu
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"; Tasks: startmenu
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandirs; Name: "{app}\launcher.log"
Type: filesandirs; Name: "{app}\settings.json"

[Code]
// Custom colors for the installer wizard
procedure InitializeWizard;
begin
  // Dark background
  WizardForm.Color := $1a1a2e;

  // Main panel
  WizardForm.MainPanel.Color := $16213e;

  // Inner page
  WizardForm.InnerPage.Color := $1a1a2e;

  // Welcome page
  WizardForm.WelcomePage.Color := $1a1a2e;

  // Finished page
  WizardForm.FinishedPage.Color := $1a1a2e;

  // Header label
  WizardForm.PageNameLabel.Font.Color := $e94560;
  WizardForm.PageNameLabel.Font.Size := 14;
  WizardForm.PageNameLabel.Font.Style := [fsBold];

  // Description label
  WizardForm.PageDescriptionLabel.Font.Color := $c4c4c4;

  // Welcome labels
  WizardForm.WelcomeLabel1.Font.Color := $e94560;
  WizardForm.WelcomeLabel1.Font.Size := 16;
  WizardForm.WelcomeLabel1.Font.Style := [fsBold];
  WizardForm.WelcomeLabel2.Font.Color := $c4c4c4;

  // Finished labels
  WizardForm.FinishedHeadingLabel.Font.Color := $e94560;
  WizardForm.FinishedHeadingLabel.Font.Size := 16;
  WizardForm.FinishedHeadingLabel.Font.Style := [fsBold];
  WizardForm.FinishedLabel.Font.Color := $c4c4c4;

  // Buttons
  WizardForm.NextButton.Font.Color := $ffffff;
  WizardForm.BackButton.Font.Color := $ffffff;
  WizardForm.CancelButton.Font.Color := $ffffff;

  // Directory edit
  WizardForm.DirEdit.Color := $0f3460;
  WizardForm.DirEdit.Font.Color := $ffffff;

  // Components list
  WizardForm.TasksList.Color := $0f3460;
  WizardForm.TasksList.Font.Color := $ffffff;

  // Progress bar color
  WizardForm.ProgressGauge.BackColor := $0f3460;
end;
