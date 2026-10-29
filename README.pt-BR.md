# 🎧 HeadsetPlus Studio — Suíte Universal de Áudio para Windows 11

> **Language / Idioma:** 🇺🇸 [English](README.md) | 🇧🇷 **Português (Brasil)**

[![Windows 11](https://img.shields.io/badge/Windows%2011-Compatível-0078D4?style=for-the-badge&logo=windows11&logoColor=white)](https://microsoft.com)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Equalizer APO](https://img.shields.io/badge/Equalizer%20APO-Integrado-brightgreen?style=for-the-badge)](https://sourceforge.net/projects/equalizerapo/)
[![CI Quality Gate](https://img.shields.io/badge/CI%20Audit-100%25%20Aprovado-success?style=for-the-badge&logo=githubactions&logoColor=white)](.github/workflows/ci.yml)
[![Author](https://img.shields.io/badge/Criado%20Por-Matheus%20Veras-orange?style=for-the-badge)](LICENSE.md)

> **Suíte Universal de Controle Acústico Avançado, DSP Global para Windows 11, Áudio Espacial 3D e Telemetria em Tempo Real para Fones Sony, AirPods, Galaxy Buds, Bose e Multimarca.**

Desenvolvido e arquitetado por **Matheus Veras**, o **HeadsetPlus Studio** é a central de áudio universal definitiva para Windows 11. O aplicativo eleva qualquer fone de ouvido—seja Bluetooth, USB ou P2/3.5mm—com arquitetura limpa de padrão industrial, motor DSP paramétrico de 64 bits, calibração audiophile com +5.000 fones (AutoEq), overlay flutuante nativo e integração profunda com as APIs nativas do Windows 11.

---

## ✨ Principais Funcionalidades

### 💎 1. Interface Gráfica Obsidian Glassmorphism (WebView2)
* **Design Hi-Fi:** Interface inspirada nos estúdios da Logitech G HUB e no design translúcido Fluent do Windows 11.
* **Curva de Frequência B-Spline Interativa:** Gráfico dinâmico renderizado em tempo real via HTML5 Canvas para visualização acústica intuitiva.
* **Internacionalização Nativa (7 Idiomas):** Suporte completo para Português (`pt-BR`), Inglês (`en-US`), Japonês (`ja-JP`), Espanhol (`es-ES`), Alemão (`de-DE`), Chinês (`zh-CN`) e Francês (`fr-FR`) com detecção automática do sistema.

### 🔄 2. Ecossistema Multimarca & Arquitetura de Plugins
* **Detecção Inteligente:** Identifica automaticamente a marca e o modelo do fone conectado, seleciona o protocolo de driver adequado e adapta a interface instantaneamente.
* **Sony MDR V1 Driver:** Protocolo Serial HPC (Porta RFCOMM 9) com suporte completo ao lendário **Sony WF-1000XM3** (ANC, Modo Vento, Som Ambiente, Clear Bass e controle de sensores).
* **Sony Tandem V2 Driver:** Suporte completo aos modelos **WH-1000XM4**, **WF-1000XM4**, **WH-1000XM5** e **WF-1000XM5**.
* **Universal Windows 11 Driver:** Controle de equalização e áudio espacial para **AirPods (Apple)**, **Galaxy Buds (Samsung)**, **Bose QC**, **realme Buds** e qualquer headset gamer USB/P2.

### 🎛️ 3. Motor DSP Global Windows 11 (Equalizer APO Bridge)
* **Filtros Paramétricos Biquad 64-bit:** Equalizador acústico de 6 bandas (Clear Bass + 400Hz, 1kHz, 2.5kHz, 6.3kHz, 16kHz) atuando diretamente no kernel de áudio (`AudioDG.exe`).
* **Preamp Anti-Clipping Dinâmico:** Cálculo matemático em tempo real para evitar distorção harmônica e saturação de sinal.
* **Áudio Espacial 3D Linkwitz / Chu-Moy:** Expansão de palco sonoro binaural com simulação estéreo natural para jogos e filmes, eliminando a fadiga auditiva de fones in-ear.

### 🎯 4. Banco de Dados AutoEq Integrado (+5.000 Fones)
* Motor de busca instantâneo integrado com curvas de calibração audiophile de referência (**Harman Target**, Crinacle, Oratory1990 e Rtings) aplicáveis com apenas 1 clique.

### 🪟 5. Overlay Flutuante Nativo Estilo Apple iOS
* **Zero Roubo de Foco:** Card de alta definição renderizado diretamente sobre a Área de Trabalho ou sobre jogos em tela cheia via Win32 `UpdateLayeredWindow`.
* **Disparo Automático:** Exibe graficamente o nível de bateria das cápsulas Esquerda (L), Direita (R) e do Estojo (Case) ao retirar o fone do case ou ao sincronizar.

### ⚡ 6. Zero-Click Auto-Connect & Anti-Falsos Positivos
* Monitoramento de eventos do kernel Windows 11 (`WM_DEVICECHANGE`) para auto-conexão imediata ao retirar o fone do estojo.
* **Validação Real via Win32 `BluetoothGetDeviceInfo`:** Elimina completamente falsos positivos quando o fone está guardado no estojo ou desconectado.

### 🔋 7. System Tray Dinâmico com LED Semântico
* Ícone em tempo real na Bandeja do Sistema com LED indicativo de status:
  * 🟢 **Verde:** Bateria saudável (> 35%).
  * 🟡 **Âmbar:** Bateria média (20% - 35%).
  * 🔴 **Vermelho:** Alerta crítico (< 20%) com notificação inteligente.
  * ⚪ **Cinza:** Standby / Desconectado.
* Menu de contexto completo para troca rápida de perfis de EQ, cancelamento de ruído e DSP.

### 🩺 8. Dosímetro Auditivo & Alerta OMS (CoreAudio COM)
* Medição de pressão sonora estimada (dB SPL) com rastreamento de exposição sonora contínua em conformidade com as diretrizes da Organização Mundial da Saúde (OMS).

---

## 🏗️ Arquitetura do Software

O código foi projetado seguindo os princípios de **Engenharia de Software de Produção** e o **Princípio da Responsabilidade Única (SRP)**:

```
headsetplus-studio/
├── app/                        # Pacote Central Modular da Aplicação
│   ├── config.py               # Gerenciador de Configuração, Caminhos e Persistência Atômica
│   ├── win32_utils.py          # Integrações Win32 de Baixo Nível (Mutex, Registro DWM, Ícone, Idioma)
│   ├── tray_manager.py         # Gerenciamento da Bandeja do Sistema (LED Semântico e Telemetria)
│   ├── rpc_bridge.py           # Ponte RPC JS <-> Python (36 Métodos Fortemente Tipados)
│   └── controller.py           # Orquestrador Mestre de Todos os Subsistemas
├── core/                       # Núcleo de Drivers e Processamento de Áudio
│   ├── drivers/                # Drivers de Hardware (Sony V1, V2 e Universal Windows)
│   ├── windows_apo_engine.py   # Motor DSP Equalizer APO & Filtros Biquad
│   ├── autoeq_database.py      # Base de Dados AutoEq com +5.000 Perfis
│   ├── ios_desktop_overlay.py  # Janela Flutuante Nativa sem Foco (Win32 Alpha Premultiplicado)
│   ├── system_integration.py   # Hotkeys Globais, Automação por App e Eventos de Kernel
│   └── device_detector.py      # Detecção Nativa Bluetooth e Classificação de Protocolo
├── scripts/                    # Scripts de Manutenção, Build e Testes
│   ├── build_standalone_exe.py # Compilador do Executável Único (PyInstaller)
│   ├── package_release.py      # Empacotador de Releases (ZIP Portátil e Inno Setup)
│   └── master_audit_and_test_suite.py # Suíte de Testes Automatizada (6 Frentes)
├── ui/                         # Assets Web do Frontend (HTML5, CSS3, JS Vanilla Modular)
├── assets/                     # Renders 3D em Alta Definição e Ícones Oficiais
├── .github/workflows/ci.yml    # Pipeline de CI/CD Automatizado no GitHub Actions
├── headsetplus_studio.pyw      # Ponto de Entrada Oficial Enxuto da Aplicação (~20 linhas)
├── sony_sound_connect_pc.pyw   # Ponto de Entrada de Retrocompatibilidade
├── config.json                 # Arquivo de Preferências do Usuário (Persistência Atômica)
└── LICENSE.md                  # Licença de Propriedade do Projeto
```

---

## 🚀 Como Executar

### Opção 1: Executável Standalone Pronto (Sem Instalação)
1. Acesse a aba [Releases](https://github.com/MatheusVeras1/headsetplus-studio/releases).
2. Baixe o arquivo **`HeadsetPlus-Studio-v1.0.0-Windows-Portable.zip`** ou o instalador **`HeadsetPlus-Studio-v1.0.0-Setup.exe`**.
3. Execute o programa dando dois cliques no executável.

### Opção 2: A Partir do Código Fonte (Desenvolvedores)
Certifique-se de ter o **Python 3.10+** instalado no Windows 11.

```powershell
# 1. Clone o repositório
git clone https://github.com/MatheusVeras1/headsetplus-studio.git
cd headsetplus-studio

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Execute o aplicativo
python headsetplus_studio.pyw
```

---

## 🔨 Compilação e Geração de Releases

Você pode compilar o seu próprio binário `.exe` independente ou gerar os pacotes de distribuição com apenas um comando:

```powershell
# Compilação do executável único (dist/HeadsetPlusStudio.exe)
python scripts/build_standalone_exe.py

# Empacotamento do ZIP portátil e script de instalação (Inno Setup)
python scripts/package_release.py
```

---

## 🧪 Suíte de Testes Automatizada (Quality Gate)

O projeto conta com uma suíte master de testes contínuos cobrindo 6 frentes fundamentais:

```powershell
python scripts/master_audit_and_test_suite.py
```

* **Frente 1:** Compilação e verificação de sintaxe de todos os módulos Python (.py/.pyw).
* **Frente 2:** Execução funcional de todos os 36 métodos RPC (`window.pywebview.api`).
* **Frente 3:** Verificação matemática dos filtros DSP Biquad 64-bit e busca AutoEq.
* **Frente 4:** Teste de confiabilidade de encerramento, ausência de deadlocks e reaquisição de Mutex Win32.
* **Frente 5:** Auditoria dos 106 IDs do DOM e 157 chaves de tradução nos 7 idiomas.
* **Frente 6:** Verificação de integridade dos créditos autorais e licença.

---

## 👨‍💻 Autor & Créditos

* **Idealização e Desenvolvimento:** [Matheus Veras](https://github.com/MatheusVeras1)
* **Licença:** Source-Available Proprietary (Consulte o arquivo [LICENSE.md](LICENSE.md) para detalhes).
* **Agradecimentos Especiais:** À comunidade open-source do Equalizer APO e ao projeto AutoEq de Jaakko Pasanen.
