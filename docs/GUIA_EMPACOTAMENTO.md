# Guia de Empacotamento - Controle Financeiro

## Visão Geral

Este guia explica como criar um executável (.exe) do sistema Controle Financeiro para distribuição.

## Pré-requisitos

1. **Python 3.11+** instalado
2. **Todas as dependências** instaladas:
   ```bash
   pip install -r requirements.txt
   ```
3. **PyInstaller** instalado (já incluído no requirements.txt)

## Método Rápido: Script Automatizado

### Windows

Execute o script de build:

```bash
.\build.bat
```

O script irá:
1. Limpar builds anteriores
2. Limpar cache do Python
3. Verificar/instalar PyInstaller
4. Compilar a aplicação usando `python -m PyInstaller`
5. **Copiar automaticamente o `config.env` para `dist\ControleFinanceiro\`**
6. Criar o executável em `dist/ControleFinanceiro/ControleFinanceiro.exe`

**Tempo estimado**: 3-5 minutos

**IMPORTANTE**: 
- O executável será criado em uma pasta (`dist/ControleFinanceiro/`) e não como arquivo único. Isso é necessário para evitar problemas com NumPy e outras bibliotecas.
- O `config.env` agora é copiado automaticamente pelo `build.bat`. Você não precisa mais copiar manualmente!

## Método Manual

### 1. Limpar Cache

```bash
# Limpar builds anteriores
rmdir /s /q build
rmdir /s /q dist

# Limpar cache Python
for /r %i in (*.pyc) do del "%i"
for /d /r %i in (__pycache__) do rmdir /s /q "%i"
```

### 2. Executar PyInstaller

```bash
python -m PyInstaller --clean --noconfirm ControleFinanceiro.spec
```

**Nota**: Use `python -m PyInstaller` ao invés de apenas `pyinstaller` para evitar problemas de PATH no Windows.

### 3. Testar o Executável

```bash
dist\ControleFinanceiro\ControleFinanceiro.exe
```

**Nota**: O executável está dentro da pasta `dist/ControleFinanceiro/` e precisa de todos os arquivos dessa pasta para funcionar.

## Estrutura do Arquivo .spec

O arquivo `ControleFinanceiro.spec` contém a configuração do build:

```python
# Principais configurações:
- name='ControleFinanceiro'  # Nome do executável
- console=False              # Sem janela de console
- upx=True                   # Compressão UPX ativada
- optimize=2                 # Otimização máxima
- excludes=['tkinter']       # Excluir módulos não usados
```

### Assets Incluídos

- `assets/` - Estilos, ícones e recursos visuais

### Hidden Imports

Módulos que precisam ser incluídos explicitamente:
- PyQt6 (Core, Gui, Widgets)
- Matplotlib
- Supabase e dependências
- Pydantic
- Bcrypt

## Distribuição

### Formato: Pasta com Executável

O build cria uma pasta `dist/ControleFinanceiro/` contendo:
- `ControleFinanceiro.exe` - Executável principal
- DLLs e bibliotecas necessárias
- Assets e recursos
- `config.env` - Arquivo de configuração (copiado automaticamente pelo build.bat)

**IMPORTANTE**: Distribua a pasta completa, não apenas o .exe!

**Vantagens:**
- Startup mais rápido
- Compatibilidade melhor com NumPy/Matplotlib
- Mais fácil de debugar

**Como distribuir:**
1. Comprima a pasta `dist/ControleFinanceiro/` em um arquivo .zip
2. Distribua o .zip
3. Usuário descompacta e executa `ControleFinanceiro.exe`

### Configuração do config.env

O sistema precisa de um arquivo `config.env` na mesma pasta do executável com as seguintes variáveis:

```env
SUPABASE_URL=sua_url_do_supabase
SUPABASE_KEY=sua_chave_do_supabase
CHAVE_MESTRA=sua_chave_de_criptografia
```

**Como funciona:**

1. **Durante o build**:
   - O `build.bat` copia automaticamente o `config.env` da raiz do projeto para `dist\ControleFinanceiro\`
   - Você não precisa copiar manualmente

2. **Durante a execução**:
   - O executável detecta automaticamente se está rodando como `.exe` empacotado
   - Busca o `config.env` no mesmo diretório do executável
   - Carrega as variáveis de ambiente do arquivo

**CRÍTICO**: O `config.env` deve existir na raiz do projeto antes de executar `build.bat`. Caso contrário, o executável não funcionará e mostrará o erro:
```
ValueError: ERRO: Variáveis de ambiente SUPABASE_URL e SUPABASE_KEY são obrigatórias.
```

## Tamanho do Executável

**Tamanho esperado**: ~150-200 MB

Isso inclui:
- Python runtime
- PyQt6
- Matplotlib
- Todas as bibliotecas
- Assets

### Reduzir Tamanho (Opcional)

Para reduzir o tamanho, você pode:

1. **Remover módulos não usados** no .spec:
   ```python
   excludes=['tkinter', 'test', 'unittest', 'email', 'xml']
   ```

2. **Usar UPX** (já ativado):
   ```python
   upx=True
   ```

3. **Otimizar bytecode**:
   ```python
   optimize=2
   ```

## Problemas Comuns

### 1. "ERRO: Variáveis de ambiente SUPABASE_URL e SUPABASE_KEY são obrigatórias"

**Causa**: Arquivo `.env` não encontrado ou não incluído no build

**Solução**:
- **Opção A**: Incluir `.env` no build (distribuição interna)
  1. Crie o arquivo `.env` na raiz do projeto com suas credenciais
  2. Execute `.\build.bat` novamente
  3. O `.env` será incluído automaticamente

- **Opção B**: Criar `.env` manualmente (distribuição pública)
  1. Copie o arquivo `.env.example` para a pasta do executável
  2. Renomeie para `.env`
  3. Edite e adicione suas credenciais do Supabase

### 2. "pyinstaller não é reconhecido"

**Causa**: PyInstaller não está no PATH do Windows

**Solução**: Use `python -m PyInstaller` ao invés de apenas `pyinstaller`:
```bash
python -m PyInstaller --clean --noconfirm ControleFinanceiro.spec
```

O script `build.bat` já usa este método.

### 3. "TypeError: argument docstring of add_docstring should be a str"

**Causa**: Incompatibilidade entre NumPy e PyInstaller com otimização

**Solução**: Já corrigido no .spec:
- `optimize=0` (desativa otimização)
- `exclude_binaries=True` (cria pasta ao invés de arquivo único)
- Hidden imports do NumPy adicionados

### 4. "Module not found"

**Solução**: Adicione o módulo em `hiddenimports` no .spec:
```python
hiddenimports=['nome_do_modulo']
```

### 5. "Assets não encontrados"

**Solução**: Verifique se a pasta assets está incluída:
```python
datas=[('assets', 'assets')]
```

### 6. Executável não abre

**Solução**: Execute com console para ver erros:
```python
console=True  # Temporariamente no .spec
```

### 7. Erro de DLL

**Solução**: Instale Visual C++ Redistributable:
- [Download Microsoft](https://aka.ms/vs/17/release/vc_redist.x64.exe)

## Teste Antes de Distribuir

### Checklist de Testes:

- [ ] Executável abre sem erros
- [ ] Login funciona
- [ ] Dashboard carrega
- [ ] Todas as telas abrem
- [ ] Banco de dados é criado corretamente
- [ ] Operações CRUD funcionam
- [ ] Relatórios são gerados
- [ ] Gráficos são exibidos
- [ ] Backup/Restore funcionam

## Versioning

Atualize a versão em:
1. `ui/main_window.py` - Variável `VERSION_ATUAL`
2. Nome do executável (opcional)

## Distribuição para Usuários

### Instruções para o Usuário:

1. **Download**: Baixe o arquivo `ControleFinanceiro.zip`
2. **Extrair**: Descompacte o arquivo em uma pasta de sua escolha
3. **Executar**: Abra a pasta e duplo clique em `ControleFinanceiro.exe`
4. **Primeiro Uso**: 
   - Crie uma conta
   - Configure suas categorias
   - Comece a usar!

**IMPORTANTE**: Não mova apenas o .exe, mantenha todos os arquivos da pasta juntos!

### Requisitos do Sistema:

- **OS**: Windows 10/11 (64-bit)
- **RAM**: 4 GB mínimo (8 GB recomendado)
- **Espaço**: 500 MB livres
- **Resolução**: 1280x720 mínimo

## Atualizações

O sistema verifica automaticamente por atualizações no GitHub.

Para criar uma nova versão:
1. Atualize `VERSION_ATUAL` no código
2. Compile novo executável
3. Faça upload no GitHub Releases
4. Atualize `version.txt` no repositório

## Logs e Debug

Logs são salvos em:
```
C:\Users\<usuario>\AppData\Local\ControleFinanceiro\logs\
```

Para debug, ative o console temporariamente:
```python
console=True  # em ControleFinanceiro.spec
```

## Performance

### Otimizações Aplicadas:

1. **Lazy Loading** - Telas carregadas sob demanda
2. **UPX Compression** - Executável comprimido
3. **Bytecode Optimization** - Código otimizado (level 2)
4. **Exclusão de módulos** - Tkinter e outros removidos

### Resultado:

- Startup: ~1-2 segundos
- Memória inicial: ~50-80 MB
- Troca de telas: Instantânea

## Suporte

Para problemas com o empacotamento:
1. Verifique os logs do PyInstaller
2. Teste com `console=True`
3. Verifique dependências no requirements.txt
4. Consulte a documentação do PyInstaller

## Data de Criação

03/03/2026

## Relacionado

- `ControleFinanceiro.spec` - Configuração do build
- `build.bat` - Script de build automatizado
- `requirements.txt` - Dependências do projeto
