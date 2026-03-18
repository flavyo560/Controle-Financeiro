#define MyAppName "Controle Financeiro"
#define MyAppVersion "2.5"
#define MyAppExeName "ControleFinanceiro.exe"
#define MyAppPublisher "Seu Nome"
#define MyAppURL "https://github.com/seu-usuario/seu-repo"

[Setup]
AppId={{EEF5A654-8DA5-4C91-807D-21D42A7902EC}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
; Diretório de saída do instalador
OutputDir=.
; Nome do arquivo de saída
OutputBaseFilename=Instalador_ControleFinanceiro_v{#MyAppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
; Ícone do instalador (se tiver)
SetupIconFile=assets\icon.ico
; Ícone do desinstalador
UninstallDisplayIcon={app}\{#MyAppExeName}

; --- CONFIGURAÇÕES PARA ATUALIZAÇÃO AUTOMÁTICA ---
; Fecha o aplicativo automaticamente se ele estiver aberto durante a instalação
CloseApplications=yes
; Garante que a instalação ocorra por cima da antiga
RestartApplications=yes

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Copiar toda a pasta dist\ControleFinanceiro para {app}
Source: "dist\ControleFinanceiro\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[InstallDelete]
; Remove atalhos antigos antes de criar novos
Type: files; Name: "{autodesktop}\Controle Financeiro.lnk"
Type: files; Name: "{autodesktop}\{#MyAppName}.lnk"
Type: files; Name: "{autoprograms}\Controle Financeiro.lnk"
Type: files; Name: "{autoprograms}\{#MyAppName}.lnk"

[Run]
; Abre o app após instalar (mas não em atualizações silenciosas)
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Limpar arquivos de dados do usuário (opcional - comente se quiser preservar dados)
; Type: filesandordirs; Name: "{localappdata}\ControleFinanceiro"
