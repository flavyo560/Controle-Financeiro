# Guia de Criação do Instalador - Controle Financeiro

## Visão Geral

Este guia explica como criar um instalador profissional (.exe) usando Inno Setup para distribuir o sistema Controle Financeiro.

## Pré-requisitos

### 1. Inno Setup 6

Baixe e instale o Inno Setup:
- **Download**: https://jrsoftware.org/isdl.php
- **Versão**: 6.x ou superior
- **Instalação**: Padrão (C:\Program Files (x86)\Inno Setup 6\)

### 2. Executável Compilado

Certifique-se de ter o executável compilado:
```bash
.\build.bat
```

Isso criará a pasta `dist\ControleFinanceiro\` com todos os arquivos necessários.

## Método Rápido: Script Automatizado

### Windows

Execute o script de build do instalador:

```bash
.\build_installer.bat
```

O script irá:
1. Verificar se o Inno Setup está instalado
2. Verificar se a pasta `dist\ControleFinanceiro` existe
3. Compilar o instalador usando `installer.iss`
4. Criar o arquivo `Instalador_ControleFinanceiro_v2.3.exe`

**Tempo estimado**: 30 segundos

## Método Manual

### 1. Abrir o Inno Setup

1. Abra o Inno Setup Compiler
2. File → Open → Selecione `installer.iss`

### 2. Compilar

1. Build → Compile (ou pressione F9)
2. Aguarde a compilação
3. O instalador será criado na raiz do projeto

### 3. Testar

Execute o instalador gerado:
```bash
Instalador_ControleFinanceiro_v2.3.exe
```

## Estrutura do Arquivo installer.iss

### Configurações Principais

```ini
[Setup]
AppName=Controle Financeiro
AppVersion=2.3
DefaultDirName={autopf}\Controle Financeiro
OutputBaseFilename=Instalador_ControleFinanceiro_v2.3
```

### Arquivos Incluídos

```ini
[Files]
Source: "dist\ControleFinanceiro\*"
DestDir: "{app}"
Flags: ignoreversion recursesubdirs createallsubdirs
```

Isso copia toda a pasta `dist\ControleFinanceiro\` para o diretório de instalação, incluindo:
- `ControleFinanceiro.exe` - Executável principal
- `config.env` - Configurações do Supabase (copiado automaticamente pelo build.bat)
- `assets/` - Ícones e estilos
- DLLs e bibliotecas necessárias

**IMPORTANTE**: O `config.env` já está incluído na pasta `dist\ControleFinanceiro\` após executar `build.bat`, então o instalador o incluirá automaticamente.

### Ícones Criados

- **Menu Iniciar**: Atalho no menu de programas
- **Área de Trabalho**: Atalho opcional (usuário escolhe)

### Atualização Automática

O instalador está configurado para:
- Fechar o app automaticamente se estiver aberto
- Instalar por cima da versão antiga
- Preservar dados do usuário

## Personalização

### Alterar Versão

Edite `installer.iss`:
```ini
#define MyAppVersion "2.4"
```

### Alterar Ícone

O instalador usa o ícone em `assets/icon.ico`. Para alterar:
```ini
SetupIconFile=assets\seu_icone.ico
```

### Alterar Nome do Instalador

```ini
OutputBaseFilename=Instalador_ControleFinanceiro_v2.4
```

### Adicionar Licença

Adicione uma seção `[LicenseFile]`:
```ini
[Setup]
LicenseFile=LICENSE.txt
```

### Adicionar README

Adicione uma seção `[InfoBefore]`:
```ini
[Setup]
InfoBeforeFile=README.txt
```

## Distribuição

### Tamanho do Instalador

**Tamanho esperado**: ~80-120 MB (comprimido)

O Inno Setup usa compressão LZMA, que reduz significativamente o tamanho.

### Onde Distribuir

1. **GitHub Releases**:
   - Faça upload do instalador
   - Crie uma release com notas de versão
   - Usuários baixam diretamente

2. **Google Drive / Dropbox**:
   - Faça upload do instalador
   - Compartilhe o link

3. **Site Próprio**:
   - Hospede o instalador
   - Forneça link de download

### Instruções para o Usuário

1. **Download**: Baixe `Instalador_ControleFinanceiro_v2.3.exe`
2. **Executar**: Duplo clique no arquivo
3. **Instalar**: Siga o assistente de instalação
4. **Usar**: O app será instalado e um atalho criado

## Atualização de Versão

Para criar uma nova versão:

1. **Atualizar código**:
   - Faça as alterações necessárias
   - Teste completamente

2. **Atualizar versão**:
   - Edite `installer.iss` → `MyAppVersion`
   - Edite `ui/main_window.py` → `VERSION_ATUAL`

3. **Compilar executável**:
   ```bash
   .\build.bat
   ```

4. **Compilar instalador**:
   ```bash
   .\build_installer.bat
   ```

5. **Distribuir**:
   - Faça upload do novo instalador
   - Notifique os usuários

## Instalação Silenciosa

Para instalar sem interface gráfica (útil para empresas):

```bash
Instalador_ControleFinanceiro_v2.3.exe /SILENT
```

Ou completamente silencioso:

```bash
Instalador_ControleFinanceiro_v2.3.exe /VERYSILENT
```

## Desinstalação

O instalador cria automaticamente um desinstalador em:
```
C:\Program Files\Controle Financeiro\unins000.exe
```

Ou pelo Painel de Controle:
- Configurações → Apps → Controle Financeiro → Desinstalar

## Logs de Instalação

Em caso de problemas, os logs ficam em:
```
%TEMP%\Setup Log YYYY-MM-DD #XXX.txt
```

## Problemas Comuns

### 1. "Inno Setup não encontrado"

**Solução**: Instale o Inno Setup 6 de https://jrsoftware.org/isdl.php

### 2. "Pasta dist\ControleFinanceiro não encontrada"

**Solução**: Execute `.\build.bat` primeiro para criar o executável

### 3. "Erro ao compilar"

**Solução**: 
- Verifique se todos os caminhos em `installer.iss` estão corretos
- Verifique se o arquivo `assets/icon.ico` existe
- Abra `installer.iss` no Inno Setup Compiler para ver erros detalhados

### 4. "Instalador não executa"

**Solução**:
- Verifique se o Windows Defender não está bloqueando
- Execute como Administrador
- Verifique se o arquivo não está corrompido

## Assinatura Digital (Opcional)

Para adicionar assinatura digital ao instalador:

1. **Obter certificado**:
   - Compre um certificado de code signing
   - Ou use um certificado auto-assinado para testes

2. **Configurar no Inno Setup**:
   ```ini
   [Setup]
   SignTool=signtool
   SignedUninstaller=yes
   ```

3. **Assinar**:
   ```bash
   signtool sign /f certificado.pfx /p senha Instalador_ControleFinanceiro_v2.3.exe
   ```

## Checklist de Distribuição

Antes de distribuir o instalador:

- [ ] Versão atualizada em `installer.iss`
- [ ] Versão atualizada em `ui/main_window.py`
- [ ] Executável compilado e testado
- [ ] Instalador compilado
- [ ] Instalador testado em máquina limpa
- [ ] Ícone correto
- [ ] Todas as funcionalidades testadas
- [ ] Documentação atualizada
- [ ] Notas de versão preparadas

## Suporte

Para problemas com o instalador:
1. Verifique os logs de instalação
2. Teste em modo verbose: `/LOG="install.log"`
3. Consulte a documentação do Inno Setup

## Data de Criação

03/03/2026

## Relacionado

- `installer.iss` - Configuração do instalador
- `build_installer.bat` - Script de build automatizado
- `build.bat` - Script de build do executável
- `docs/GUIA_EMPACOTAMENTO.md` - Guia de empacotamento
