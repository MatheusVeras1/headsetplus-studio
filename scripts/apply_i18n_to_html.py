# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open("index.html", "r", encoding="utf-8") as f:
    content = f.read()

replacements = [
    # Navigation
    ('data-tooltip="Equalizador & Acústica (1)" onclick="switchView(\'eq\', 0, false)"',
     'data-tooltip="Equalizador & Acústica (1)" data-i18n-tooltip="nav.eq" onclick="switchView(\'eq\', 0, false)"'),
    ('data-tooltip="Cancelamento de Ruído & Ambiente (2)" onclick="switchView(\'nc\', 1, false)"',
     'data-tooltip="Cancelamento de Ruído & Ambiente (2)" data-i18n-tooltip="nav.nc" onclick="switchView(\'nc\', 1, false)"'),

    # Header
    ('<span class="sony-pill" id="brandPill">SONY AUDIO</span>',
     '<span class="sony-pill" id="brandPill" data-i18n="header.brand">SONY AUDIO</span>'),
    ('<button class="device-select-btn" onclick="toggleDeviceSelector(event)" title="Alternar driver e fone de ouvido conectado">',
     '<button class="device-select-btn" onclick="toggleDeviceSelector(event)" title="Alternar driver e fone de ouvido conectado" data-i18n-title="header.device_select_title">'),
    ('<span id="lblSafetyChip">Silêncio • OMS OK</span>',
     '<span id="lblSafetyChip" data-i18n="header.safety_chip_ok">Silêncio • OMS OK</span>'),
    ('title="Monitor de Saúde Auditiva dB SPL (CoreAudio OMS)">',
     'title="Monitor de Saúde Auditiva dB SPL (CoreAudio OMS)" data-i18n-title="header.safety_chip_title">'),
    ('id="btnDesktopOverlay" onclick="triggerNativeDesktopOverlay()" title="Testar Overlay Flutuante Nativo sobre o Desktop/Jogos Windows 11">\n            <span>🪟 Overlay Win11</span>',
     'id="btnDesktopOverlay" onclick="triggerNativeDesktopOverlay()" title="Testar Overlay Flutuante Nativo sobre o Desktop/Jogos Windows 11" data-i18n-title="header.overlay_btn_title">\n            <span data-i18n="header.overlay_btn">🪟 Overlay Win11</span>'),
    ('id="btnIosPopup" onclick="showIosBatteryPopup()" title="Visualizar Card Estilo Apple iOS">\n            <span>📱 Card iOS</span>',
     'id="btnIosPopup" onclick="showIosBatteryPopup()" title="Visualizar Card Estilo Apple iOS" data-i18n-title="header.card_ios_title">\n            <span data-i18n="header.card_ios">📱 Card iOS</span>'),
    ('<span id="connText">Conectando...</span>',
     '<span id="connText" data-i18n="header.connecting">Conectando...</span>'),
    ('id="btnSync" onclick="triggerReconnect()">\n            <span>🔄 Sincronizar</span>',
     'id="btnSync" onclick="triggerReconnect()">\n            <span data-i18n="header.sync_btn">🔄 Sincronizar</span>'),

    # iOS Popup Labels
    ('<span class="ios-slot-label">Esquerdo</span>',
     '<span class="ios-slot-label" data-i18n="hero.left_short">Esquerdo</span>'),
    ('<span class="ios-slot-label">Estojo</span>',
     '<span class="ios-slot-label" data-i18n="hero.case_short">Estojo</span>'),
    ('<span class="ios-slot-label">Direito</span>',
     '<span class="ios-slot-label" data-i18n="hero.right_short">Direito</span>'),

    # Hero Deck
    ('<span class="channel-badge">L</span>\n              <span class="hw-name">Fone Esquerdo</span>',
     '<span class="channel-badge">L</span>\n              <span class="hw-name" data-i18n="hero.left">Fone Esquerdo</span>'),
    ('<span class="hw-sub" id="subLeft">Canal Mestre RFCOMM</span>',
     '<span class="hw-sub" id="subLeft" data-i18n="hero.master">Canal Mestre RFCOMM</span>'),
    ('<span class="channel-badge case">CASE</span>\n              <span class="hw-name">Estojo do Fone</span>',
     '<span class="channel-badge case">CASE</span>\n              <span class="hw-name" data-i18n="hero.case">Estojo do Fone</span>'),
    ('<span class="hw-sub" id="subCase">Carga da Bateria</span>',
     '<span class="hw-sub" id="subCase" data-i18n="hero.case_charge">Carga da Bateria</span>'),
    ('<span class="channel-badge right">R</span>\n              <span class="hw-name">Fone Direito</span>',
     '<span class="channel-badge right">R</span>\n              <span class="hw-name" data-i18n="hero.right">Fone Direito</span>'),
    ('<span class="hw-sub" id="subRight">Sincronização True Wireless</span>',
     '<span class="hw-sub" id="subRight" data-i18n="hero.sync">Sincronização True Wireless</span>'),

    # View 1: Equalizer
    ('<span class="micro-label">MOTOR ACÚSTICO DSP DE 6 BANDAS</span>\n                <h2 class="section-title" style="font-size: 0.98rem;">Curva de Resposta em Frequência</h2>',
     '<span class="micro-label" data-i18n="eq.engine_title">MOTOR ACÚSTICO DSP DE 6 BANDAS</span>\n                <h2 class="section-title" style="font-size: 0.98rem;" data-i18n="eq.curve_title">Curva de Resposta em Frequência</h2>'),
    ('<button class="btn" onclick="resetEqFlat()">⭕ Resetar 0 dB</button>',
     '<button class="btn" onclick="resetEqFlat()" data-i18n="eq.reset_btn">⭕ Resetar 0 dB</button>'),
    ('<span class="micro-label" id="lblSubTabCategory">DSP ACOUSTIC LIBRARY</span>\n                <h2 class="section-title" style="font-size: 0.94rem;" id="lblSubTabTitle">Perfis & Presets</h2>',
     '<span class="micro-label" id="lblSubTabCategory" data-i18n="eq.presets_title">DSP ACOUSTIC LIBRARY</span>\n                <h2 class="section-title" style="font-size: 0.94rem;" id="lblSubTabTitle" data-i18n="eq.presets_sub">Perfis & Presets</h2>'),
    ('<button class="btn btn-copper" style="padding: 4px 9px; font-size: 0.72rem;" onclick="saveCurrentAsCustomProfile()">\n                💾 Salvar\n              </button>',
     '<button class="btn btn-copper" style="padding: 4px 9px; font-size: 0.72rem;" onclick="saveCurrentAsCustomProfile()" data-i18n="eq.save_btn">\n                💾 Salvar\n              </button>'),
    ('<button class="seg-tab active" id="segBtnPresets" onclick="switchPresetSubTab(\'presets\')">⚡ Presets G HUB</button>\n              <button class="seg-tab" id="segBtnAutoEq" onclick="switchPresetSubTab(\'autoeq\')">🎯 AutoEq™ (+5.000)</button>',
     '<button class="seg-tab active" id="segBtnPresets" onclick="switchPresetSubTab(\'presets\')" data-i18n="eq.tab_presets">⚡ Presets G HUB</button>\n              <button class="seg-tab" id="segBtnAutoEq" onclick="switchPresetSubTab(\'autoeq\')" data-i18n="eq.tab_autoeq">🎯 AutoEq™ (+5.000)</button>'),
    ('<div class="preset-name">⭐ Audiófilo (Comunidade)</div>\n                  <div class="preset-desc">Clear Bass +3 • Palco & Detalhe Vocal</div>',
     '<div class="preset-name" data-i18n="eq.preset_audiophile_name">⭐ Audiófilo (Comunidade)</div>\n                  <div class="preset-desc" data-i18n="eq.preset_audiophile_desc">Clear Bass +3 • Palco & Detalhe Vocal</div>'),
    ('<div class="preset-name">🔥 Empolgado (Meu Perfil)</div>\n                  <div class="preset-desc">Clear Bass +8 • Graves Fortes & Brilho</div>',
     '<div class="preset-name" data-i18n="eq.preset_excited_name">🔥 Empolgado (Meu Perfil)</div>\n                  <div class="preset-desc" data-i18n="eq.preset_excited_desc">Clear Bass +8 • Graves Fortes & Brilho</div>'),
    ('<div class="preset-name">🎮 Gaming FPS (Passos)</div>\n                  <div class="preset-desc">Clear Bass -2 • Foco em Passos 2.5–6.3kHz</div>',
     '<div class="preset-name" data-i18n="eq.preset_fps_name">🎮 Gaming FPS (Passos)</div>\n                  <div class="preset-desc" data-i18n="eq.preset_fps_desc">Clear Bass -2 • Foco em Passos 2.5–6.3kHz</div>'),
    ('<div class="preset-name">🎙️ Voz & Podcast</div>\n                  <div class="preset-desc">Clear Bass -1 • Nitidez de Fala</div>',
     '<div class="preset-name" data-i18n="eq.preset_vocal_name">🎙️ Voz & Podcast</div>\n                  <div class="preset-desc" data-i18n="eq.preset_vocal_desc">Clear Bass -1 • Nitidez de Fala</div>'),
    ('<div class="preset-name">🎬 Cinema Sub-Bass</div>\n                  <div class="preset-desc">Clear Bass +9 • Impacto de Subgraves</div>',
     '<div class="preset-name" data-i18n="eq.preset_bass_name">🎬 Cinema Sub-Bass</div>\n                  <div class="preset-desc" data-i18n="eq.preset_bass_desc">Clear Bass +9 • Impacto de Subgraves</div>'),
    ('placeholder="Buscar modelo (Sony, AirPods, Buds...)" oninput="onAutoEqSearch(this.value)"',
     'placeholder="Buscar modelo (Sony, AirPods, Buds...)" data-i18n-placeholder="eq.autoeq_placeholder" oninput="onAutoEqSearch(this.value)"'),
    ('<button class="brand-pill active" onclick="selectAutoEqBrand(\'all\', this)">Todos</button>',
     '<button class="brand-pill active" onclick="selectAutoEqBrand(\'all\', this)" data-i18n="eq.autoeq_all">Todos</button>'),

    # View 2: Noise Control
    ('<span class="micro-label">PROCESSADOR HD DE CANCELAMENTO DE RUÍDO QN1e / V2</span>\n                <h2 class="section-title" style="font-size: 1.02rem;">Controle Acústico de Ruído & Ambiente</h2>',
     '<span class="micro-label" data-i18n="nc.chip_label">PROCESSADOR HD DE CANCELAMENTO DE RUÍDO QN1e / V2</span>\n                <h2 class="section-title" style="font-size: 1.02rem;" data-i18n="nc.title">Controle Acústico de Ruído & Ambiente</h2>'),
    ('<div style="font-weight: 700; font-size: 0.9rem;">Cancelamento (ANC)</div>\n                <div style="font-size: 0.74rem; color: var(--text-secondary);">Isolamento acústico máximo por inversão de onda com microfones duplos.</div>',
     '<div style="font-weight: 700; font-size: 0.9rem;" data-i18n="nc.anc">Cancelamento (ANC)</div>\n                <div style="font-size: 0.74rem; color: var(--text-secondary);" data-i18n="nc.anc_desc">Isolamento acústico máximo por inversão de onda com microfones duplos.</div>'),
    ('<div style="font-weight: 700; font-size: 0.9rem;">Redução de Vento</div>\n                <div style="font-size: 0.74rem; color: var(--text-secondary);">Desativa o microfone frontal externo para eliminar ruído de vento.</div>',
     '<div style="font-weight: 700; font-size: 0.9rem;" data-i18n="nc.wind">Redução de Vento</div>\n                <div style="font-size: 0.74rem; color: var(--text-secondary);" data-i18n="nc.wind_desc">Desativa o microfone frontal externo para eliminar ruído de vento.</div>'),
    ('<div style="font-weight: 700; font-size: 0.9rem;">Som Ambiente</div>\n                <div style="font-size: 0.74rem; color: var(--text-secondary);">Modo transparência ajustável (Nível 1 a 20) com captação de voz.</div>',
     '<div style="font-weight: 700; font-size: 0.9rem;" data-i18n="nc.ambient">Som Ambiente</div>\n                <div style="font-size: 0.74rem; color: var(--text-secondary);" data-i18n="nc.ambient_desc">Modo transparência ajustável (Nível 1 a 20) com captação de voz.</div>'),
    ('<div style="font-weight: 700; font-size: 0.9rem;">ANC Desligado</div>\n                <div style="font-size: 0.74rem; color: var(--text-secondary);">Isolamento passivo puro para máxima duração da bateria.</div>',
     '<div style="font-weight: 700; font-size: 0.9rem;" data-i18n="nc.off">ANC Desligado</div>\n                <div style="font-size: 0.74rem; color: var(--text-secondary);" data-i18n="nc.off_desc">Isolamento passivo puro para máxima duração da bateria.</div>'),
    ('<span class="micro-label">TRANSPARÊNCIA ACÚSTICA</span>\n                  <div style="font-weight: 700; font-size: 0.92rem;">\n                    Nível do Som Ambiente: <span id="lblAsmVal" class="tabular" style="color: var(--ghub-cyan);">10</span> / 20\n                  </div>',
     '<span class="micro-label" data-i18n="nc.asm_box">TRANSPARÊNCIA ACÚSTICA</span>\n                  <div style="font-weight: 700; font-size: 0.92rem;">\n                    <span data-i18n="nc.asm_level_prefix">Nível do Som Ambiente:</span> <span id="lblAsmVal" class="tabular" style="color: var(--ghub-cyan);">10</span> / 20\n                  </div>'),
    ('<span style="font-size: 0.8rem; font-weight: 600;">Foco na Voz Humana</span>',
     '<span style="font-size: 0.8rem; font-weight: 600;" data-i18n="nc.voice_focus">Foco na Voz Humana</span>'),

    # View 3: Hardware
    ('<span class="micro-label">PROCESSAMENTO INTERNO & SENSORES</span>\n              <h2 class="section-title" style="font-size: 0.98rem;">Comportamento do Hardware</h2>',
     '<span class="micro-label" data-i18n="hw.micro">PROCESSAMENTO INTERNO & SENSORES</span>\n              <h2 class="section-title" style="font-size: 0.98rem;" data-i18n="hw.title">Comportamento do Hardware</h2>'),
    ('<div style="font-weight: 600; font-size: 0.84rem;">Prioridade da Conexão Bluetooth</div>\n                <div style="font-size: 0.72rem; color: var(--text-secondary);">Conexão Estável evita cortes entre L e R no Windows</div>',
     '<div style="font-weight: 600; font-size: 0.84rem;" data-i18n="hw.conn_mode">Prioridade da Conexão Bluetooth</div>\n                <div style="font-size: 0.72rem; color: var(--text-secondary);" data-i18n="hw.conn_sub">Conexão Estável evita cortes entre L e R no Windows</div>'),
    ('<option value="Prioridade na Conexão Estável">Conexão Estável</option>\n                <option value="Prioridade na Qualidade do Som">Qualidade do Som</option>',
     '<option value="Prioridade na Conexão Estável" data-i18n="hw.conn_stable">Conexão Estável</option>\n                <option value="Prioridade na Qualidade do Som" data-i18n="hw.conn_quality">Qualidade do Som</option>'),
    ('<div style="font-weight: 600; font-size: 0.84rem;">DSEE HX (Upscaling Digital)</div>\n                <div style="font-size: 0.72rem; color: var(--text-secondary);">Manter OFF poupa bateria e evita dessincronia L/R</div>',
     '<div style="font-weight: 600; font-size: 0.84rem;" data-i18n="hw.dsee">DSEE HX (Upscaling Digital)</div>\n                <div style="font-size: 0.72rem; color: var(--text-secondary);" data-i18n="hw.dsee_sub">Manter OFF poupa bateria e evita dessincronia L/R</div>'),
    ('<div style="font-weight: 600; font-size: 0.84rem;">Pausar ao Retirar dos Ouvidos</div>\n                <div style="font-size: 0.72rem; color: var(--text-secondary);">Sensor infravermelho de proximidade</div>',
     '<div style="font-weight: 600; font-size: 0.84rem;" data-i18n="hw.wearing">Pausar ao Retirar dos Ouvidos</div>\n                <div style="font-size: 0.72rem; color: var(--text-secondary);" data-i18n="hw.wearing_sub">Sensor infravermelho de proximidade</div>'),
    ('<div style="font-weight: 600; font-size: 0.84rem;">Desligamento Automático</div>\n                <div style="font-size: 0.72rem; color: var(--text-secondary);">Evita que um lado desligue sozinho por falso-positivo</div>',
     '<div style="font-weight: 600; font-size: 0.84rem;" data-i18n="hw.auto_off">Desligamento Automático</div>\n                <div style="font-size: 0.72rem; color: var(--text-secondary);" data-i18n="hw.auto_off_sub">Evita que um lado desligue sozinho por falso-positivo</div>'),
    ('<option value="Não desligar">Não desligar</option>\n                <option value="Ao retirar dos ouvidos">Ao retirar dos ouvidos</option>\n                <option value="Após 5 minutos">Após 5 minutos</option>\n                <option value="Após 30 minutos">Após 30 minutos</option>\n                <option value="Após 1 hora">Após 1 hora</option>\n                <option value="Após 3 horas">Após 3 horas</option>',
     '<option value="Não desligar" data-i18n="hw.auto_off_never">Não desligar</option>\n                <option value="Ao retirar dos ouvidos" data-i18n="hw.auto_off_remove">Ao retirar dos ouvidos</option>\n                <option value="Após 5 minutos" data-i18n="hw.auto_off_5m">Após 5 minutos</option>\n                <option value="Após 30 minutos" data-i18n="hw.auto_off_30m">Após 30 minutos</option>\n                <option value="Após 1 hora" data-i18n="hw.auto_off_1h">Após 1 hora</option>\n                <option value="Após 3 horas" data-i18n="hw.auto_off_3h">Após 3 horas</option>'),
    ('<div style="font-weight: 600; font-size: 0.84rem;">🤖 Simulador Virtual (Mock Sem Fone)</div>\n                <div style="font-size: 0.72rem; color: var(--text-secondary);">Emula telemetria RFCOMM completa sem hardware físico conectado</div>',
     '<div style="font-weight: 600; font-size: 0.84rem;" data-i18n="hw.mock_title">🤖 Simulador Virtual (Mock Sem Fone)</div>\n                <div style="font-size: 0.72rem; color: var(--text-secondary);" data-i18n="hw.mock_desc">Emula telemetria RFCOMM completa sem hardware físico conectado</div>'),
    ('<span class="micro-label">MAPEAMENTO TOUCH & ENDEREÇO BLUETOOTH</span>\n                <h2 class="section-title" style="font-size: 0.98rem;">Sensores Touch & Pareamento</h2>',
     '<span class="micro-label" data-i18n="hw.touch_micro">MAPEAMENTO TOUCH & ENDEREÇO BLUETOOTH</span>\n                <h2 class="section-title" style="font-size: 0.98rem;" data-i18n="hw.touch_title">Sensores Touch & Pareamento</h2>'),
    ('<div style="font-weight: 600; font-size: 0.84rem;">Painel Touch Esquerdo (L)</div>\n                  <div style="font-size: 0.72rem; color: var(--text-secondary);">Toque no anel de cobre esquerdo</div>',
     '<div style="font-weight: 600; font-size: 0.84rem;" data-i18n="hw.touch_l">Painel Touch Esquerdo (L)</div>\n                  <div style="font-size: 0.72rem; color: var(--text-secondary);" data-i18n="hw.touch_l_sub">Toque no anel de cobre esquerdo</div>'),
    ('<div style="font-weight: 600; font-size: 0.84rem;">Painel Touch Direito (R)</div>\n                  <div style="font-size: 0.72rem; color: var(--text-secondary);">Toque no anel de cobre direito</div>',
     '<div style="font-weight: 600; font-size: 0.84rem;" data-i18n="hw.touch_r">Painel Touch Direito (R)</div>\n                  <div style="font-size: 0.72rem; color: var(--text-secondary);" data-i18n="hw.touch_r_sub">Toque no anel de cobre direito</div>'),
    ('<div style="font-weight: 600; font-size: 0.84rem;">Endereço MAC Bluetooth</div>\n                  <div style="font-size: 0.72rem; color: var(--text-secondary);">Auto-Connect Zero-Click via WM_DEVICECHANGE ativo</div>\n                </div>\n                <div style="display: flex; gap: 6px;">\n                  <input type="text" class="input-mac" id="inpMac" value="14:3F:A6:5D:DF:D5" />\n                  <button class="btn" style="padding: 6px 10px;" onclick="saveMacAddress()">Salvar</button>',
     '<div style="font-weight: 600; font-size: 0.84rem;" data-i18n="hw.mac_title">Endereço MAC Bluetooth</div>\n                  <div style="font-size: 0.72rem; color: var(--text-secondary);" data-i18n="hw.mac_sub">Auto-Connect Zero-Click via WM_DEVICECHANGE ativo</div>\n                </div>\n                <div style="display: flex; gap: 6px;">\n                  <input type="text" class="input-mac" id="inpMac" value="14:3F:A6:5D:DF:D5" />\n                  <button class="btn" style="padding: 6px 10px;" onclick="saveMacAddress()" data-i18n="hw.mac_save">Salvar</button>'),
    ('<span id="lblHoldPowerOff">⏻ Segure 1.4s para Desligar os Fones</span>',
     '<span id="lblHoldPowerOff" data-i18n="hw.power_off">⏻ Segure 1.4s para Desligar os Fones</span>'),

    # View 4: Shield & Combos
    ('<span style="font-weight: 700; font-size: 0.88rem; color: var(--text-primary);">🎛️ Motor DSP Global Windows 11 (Equalizer APO Bridge)</span>\n                  <span class="apo-status-pill" id="apoStatusPill">Script APO Ativo</span>',
     '<span style="font-weight: 700; font-size: 0.88rem; color: var(--text-primary);" data-i18n="shield.apo_title">🎛️ Motor DSP Global Windows 11 (Equalizer APO Bridge)</span>\n                  <span class="apo-status-pill" id="apoStatusPill" data-i18n="shield.apo_status">Script APO Ativo</span>'),
    ('id="lblApoSubStatus">\n                  Sincroniza Equalizador 6 Bandas, AutoEq e Crossfeed 3D Linkwitz com todo o áudio do PC (Spotify, Jogos, Navegador e qualquer marca de fone).\n                </div>',
     'id="lblApoSubStatus" data-i18n="shield.apo_desc">\n                  Sincroniza Equalizador 6 Bandas, AutoEq e Crossfeed 3D Linkwitz com todo o áudio do PC (Spotify, Jogos, Navegador e qualquer marca de fone).\n                </div>'),
    ('id="btnLinkApo" style="padding: 6px 11px; font-size: 0.72rem;" onclick="linkEqualizerApoClick()">\n                  🔗 Vincular APO\n                </button>',
     'id="btnLinkApo" style="padding: 6px 11px; font-size: 0.72rem;" onclick="linkEqualizerApoClick()" data-i18n="shield.apo_link_btn">\n                  🔗 Vincular APO\n                </button>'),
    ('<span class="micro-label">ARQUITETURA DE PROTEÇÃO ACÚSTICA WINDOWS 11</span>\n              <h2 class="section-title" style="font-size: 0.96rem; margin-bottom: 10px;">\n                Blindagem Anti-Robótico & Auto-Conexão Zero-Click\n              </h2>',
     '<span class="micro-label" data-i18n="shield.shield_micro">ARQUITETURA DE PROTEÇÃO ACÚSTICA WINDOWS 11</span>\n              <h2 class="section-title" style="font-size: 0.96rem; margin-bottom: 10px;" data-i18n="shield.shield_title">\n                Blindagem Anti-Robótico & Auto-Conexão Zero-Click\n              </h2>'),
    ('<div style="font-weight: 700; font-size: 0.82rem; color: #34d399;">A2DP Estéreo Puro (44.1 / 48 kHz)</div>\n                    <div style="font-size: 0.71rem; color: var(--text-secondary);">Canal de alta definição travado como padrão.</div>',
     '<div style="font-weight: 700; font-size: 0.82rem; color: #34d399;" data-i18n="shield.card_a2dp_title">A2DP Estéreo Puro (44.1 / 48 kHz)</div>\n                    <div style="font-size: 0.71rem; color: var(--text-secondary);" data-i18n="shield.card_a2dp_desc">Canal de alta definição travado como padrão.</div>'),
    ('<div style="font-weight: 700; font-size: 0.82rem; color: #34d399;">Hands-Free HFP Bloqueado</div>\n                    <div style="font-size: 0.71rem; color: var(--text-secondary);">Impede queda para mono 8 kHz no Discord/Jogos.</div>',
     '<div style="font-weight: 700; font-size: 0.82rem; color: #34d399;" data-i18n="shield.card_hfp_title">Hands-Free HFP Bloqueado</div>\n                    <div style="font-size: 0.71rem; color: var(--text-secondary);" data-i18n="shield.card_hfp_desc">Impede queda para mono 8 kHz no Discord/Jogos.</div>'),
    ('<div style="font-weight: 700; font-size: 0.82rem; color: #34d399;">Zero-Click Case Open (WM_DEVICECHANGE)</div>\n                    <div style="font-size: 0.71rem; color: var(--text-secondary);">Conecta e abre o Overlay iOS ao retirar do estojo (0.0% CPU).</div>',
     '<div style="font-weight: 700; font-size: 0.82rem; color: #34d399;" data-i18n="shield.card_case_title">Zero-Click Case Open (WM_DEVICECHANGE)</div>\n                    <div style="font-size: 0.71rem; color: var(--text-secondary);" data-i18n="shield.card_case_desc">Conecta e abre o Overlay iOS ao retirar do estojo (0.0% CPU).</div>'),
    ('<div style="font-weight: 700; font-size: 0.82rem; color: #34d399;">Overlay Nativo Sem Roubo de Foco</div>\n                    <div style="font-size: 0.71rem; color: var(--text-secondary);">Flutua sobre jogos em tela cheia/borderless via DWM.</div>',
     '<div style="font-weight: 700; font-size: 0.82rem; color: #34d399;" data-i18n="shield.card_overlay_title">Overlay Nativo Sem Roubo de Foco</div>\n                    <div style="font-size: 0.71rem; color: var(--text-secondary);" data-i18n="shield.card_overlay_desc">Flutua sobre jogos em tela cheia/borderless via DWM.</div>'),
    ('<button class="btn" style="padding: 6px 10px; font-size: 0.73rem;" onclick="cycleBluetoothStack()">🔄 Reiniciar BT</button>\n                <button class="btn btn-primary" style="padding: 6px 12px; font-size: 0.73rem;" onclick="runWindowsShieldFix()">🔒 Reaplicar Blindagem Win11</button>',
     '<button class="btn" style="padding: 6px 10px; font-size: 0.73rem;" onclick="cycleBluetoothStack()" data-i18n="shield.reset_bt">🔄 Reiniciar BT</button>\n                <button class="btn btn-primary" style="padding: 6px 12px; font-size: 0.73rem;" onclick="runWindowsShieldFix()" data-i18n="shield.reapply_shield">🔒 Reaplicar Blindagem Win11</button>'),
    ('<span class="micro-label">AUTOMAÇÃO INTELIGENTE POR PROCESSO (SETWINEVENTHOOK)</span>\n                <h2 class="section-title" style="font-size: 0.96rem;">Combos Automáticos por Aplicativo (EQ + ANC + Palco 3D)</h2>',
     '<span class="micro-label" data-i18n="shield.combos_micro">AUTOMAÇÃO INTELIGENTE POR PROCESSO (SETWINEVENTHOOK)</span>\n                <h2 class="section-title" style="font-size: 0.96rem;" data-i18n="shield.combos_title">Combos Automáticos por Aplicativo (EQ + ANC + Palco 3D)</h2>'),
    ('<button class="btn" style="padding: 5px 10px; font-size: 0.71rem;" onclick="scanPairedHeadsets()">🔍 Escanear Fones BT</button>',
     '<button class="btn" style="padding: 5px 10px; font-size: 0.71rem;" onclick="scanPairedHeadsets()" data-i18n="shield.scan_btn">🔍 Escanear Fones BT</button>'),
    ('placeholder="Processo (ex: cs2.exe)" />',
     'placeholder="Processo (ex: cs2.exe)" data-i18n-placeholder="shield.exe_placeholder" />'),
    ('<button class="btn btn-primary" style="padding: 6px 10px; font-size: 0.72rem;" onclick="saveAutomationRuleUI()">➕ Salvar</button>',
     '<button class="btn btn-primary" style="padding: 6px 10px; font-size: 0.72rem;" onclick="saveAutomationRuleUI()" data-i18n="shield.rule_save_btn">➕ Salvar</button>'),

    # View 5: Spatial Lab & ISO 226
    ('<span class="micro-label">MODELAGEM PSICOACÚSTICA ISO 226:2023</span>\n                <h2 class="section-title" style="font-size: 0.96rem;">Teste Auditivo Biométrico</h2>',
     '<span class="micro-label" data-i18n="spatial.bio_micro">MODELAGEM PSICOACÚSTICA ISO 226:2023</span>\n                <h2 class="section-title" style="font-size: 0.96rem;" data-i18n="spatial.bio_title">Teste Auditivo Biométrico</h2>'),
    ('<button class="btn" style="padding: 4px 8px; font-size: 0.70rem;" onclick="resetHearingTest()" title="Reiniciar calibração biométrica">↺ Refazer</button>',
     '<button class="btn" style="padding: 4px 8px; font-size: 0.70rem;" onclick="resetHearingTest()" title="Reiniciar calibração biométrica" data-i18n="spatial.redo_btn">↺ Refazer</button>'),
    ('placeholder="Nome (ex: Matheus Dia)" />',
     'placeholder="Nome (ex: Matheus Dia)" data-i18n-placeholder="spatial.bio_name_placeholder" />'),
    ('<button class="btn btn-primary" id="btnPlayTone" onclick="playCurrentTestTone()">\n                  <span>🔊 Tocar Tom Puro</span>\n                </button>',
     '<button class="btn btn-primary" id="btnPlayTone" onclick="playCurrentTestTone()">\n                  <span data-i18n="spatial.tone_play_btn">🔊 Tocar Tom Puro</span>\n                </button>'),
    ('<button class="btn" onclick="submitHearingSample(\'inaudible\')" style="flex: 1; font-size: 0.72rem; padding: 7px 6px;">❌ Inaudível (+4dB)</button>\n                <button class="btn" onclick="submitHearingSample(\'barely\')" style="flex: 1; font-size: 0.72rem; padding: 7px 6px; border-color: rgba(197,160,89,0.45);">🔉 Limiar Exato</button>\n                <button class="btn btn-copper" onclick="submitHearingSample(\'clear\')" style="flex: 1; font-size: 0.72rem; padding: 7px 6px;">✅ Claro e Nítido</button>',
     '<button class="btn" onclick="submitHearingSample(\'inaudible\')" style="flex: 1; font-size: 0.72rem; padding: 7px 6px;" data-i18n="spatial.btn_inaudible">❌ Inaudível (+4dB)</button>\n                <button class="btn" onclick="submitHearingSample(\'barely\')" style="flex: 1; font-size: 0.72rem; padding: 7px 6px; border-color: rgba(197,160,89,0.45);" data-i18n="spatial.btn_barely">🔉 Limiar Exato</button>\n                <button class="btn btn-copper" onclick="submitHearingSample(\'clear\')" style="flex: 1; font-size: 0.72rem; padding: 7px 6px;" data-i18n="spatial.btn_clear">✅ Claro e Nítido</button>'),
    ('<span style="font-weight: 700; color: var(--text-secondary);" id="lblBioCurveTitle">Curva Biométrica vs Referência Plana (0 dB)</span>',
     '<span style="font-weight: 700; color: var(--text-secondary);" id="lblBioCurveTitle" data-i18n="spatial.bio_curve_title">Curva Biométrica vs Referência Plana (0 dB)</span>'),
    ('<button class="btn btn-primary" style="padding: 5px 10px; font-size: 0.72rem; flex-shrink: 0;" onclick="applyBiometricCurveToEq()">\n                    ⚡ Aplicar no EQ\n                  </button>',
     '<button class="btn btn-primary" style="padding: 5px 10px; font-size: 0.72rem; flex-shrink: 0;" onclick="applyBiometricCurveToEq()" data-i18n="spatial.apply_eq_btn">\n                    ⚡ Aplicar no EQ\n                  </button>'),
    ('<span class="micro-label">TOPOLOGIA BIQUAD LINKWITZ / CHU-MOY & DOSÍMETRO OMS</span>\n                <h2 class="section-title" style="font-size: 0.96rem;">Áudio Espacial 3D & Saúde Auditiva</h2>',
     '<span class="micro-label" data-i18n="spatial.stage_micro">TOPOLOGIA BIQUAD LINKWITZ / CHU-MOY & DOSÍMETRO OMS</span>\n                <h2 class="section-title" style="font-size: 0.96rem;" data-i18n="spatial.stage_title">Áudio Espacial 3D & Saúde Auditiva</h2>'),
    ('<div class="sp-mode-title">Estúdio Near-Field</div>\n                  <div class="sp-mode-sub">700Hz • 280µs (60°)</div>',
     '<div class="sp-mode-title" data-i18n="spatial.mode_nearfield_title">Estúdio Near-Field</div>\n                  <div class="sp-mode-sub" data-i18n="spatial.mode_nearfield_sub">700Hz • 280µs (60°)</div>'),
    ('<div class="sp-mode-title">Sala Acústica Hi-Fi</div>\n                  <div class="sp-mode-sub">620Hz • 340µs (72°)</div>',
     '<div class="sp-mode-title" data-i18n="spatial.mode_hifi_title">Sala Acústica Hi-Fi</div>\n                  <div class="sp-mode-sub" data-i18n="spatial.mode_hifi_sub">620Hz • 340µs (72°)</div>'),
    ('<div class="sp-mode-title">Gaming 3D FPS</div>\n                  <div class="sp-mode-sub">880Hz • 220µs (52°)</div>',
     '<div class="sp-mode-title" data-i18n="spatial.mode_esports_title">Gaming 3D FPS</div>\n                  <div class="sp-mode-sub" data-i18n="spatial.mode_esports_sub">880Hz • 220µs (52°)</div>'),
    ('<span style="font-weight: 600; color: var(--text-primary);">Abertura do Palco Estéreo (Crossfeed Matrix + APO)</span>',
     '<span style="font-weight: 600; color: var(--text-primary);" data-i18n="spatial.crossfeed_label">Abertura do Palco Estéreo (Crossfeed Matrix + APO)</span>'),
    ('<button class="btn btn-primary" id="btnSpatialDemo" style="flex: 1.35; font-size: 0.73rem; padding: 7px 10px;" onclick="playSpatialDemoAudio()">\n                  <span>✨ Ouvir Demo 3D Linkwitz</span>\n                </button>',
     '<button class="btn btn-primary" id="btnSpatialDemo" style="flex: 1.35; font-size: 0.73rem; padding: 7px 10px;" onclick="playSpatialDemoAudio()">\n                  <span data-i18n="spatial.btn_demo_3d">✨ Ouvir Demo 3D Linkwitz</span>\n                </button>'),
    ('<button class="btn" id="btnSpatialAB" style="flex: 1; font-size: 0.71rem; padding: 7px 8px;" onclick="toggleSpatialABComparison()" title="Alternar entre Crossfeed 3D Biquad e Estéreo Isolado">\n                  <span>🔀 A/B: 3D HRTF ON</span>\n                </button>',
     '<button class="btn" id="btnSpatialAB" style="flex: 1; font-size: 0.71rem; padding: 7px 8px;" onclick="toggleSpatialABComparison()" title="Alternar entre Crossfeed 3D Biquad e Estéreo Isolado">\n                  <span data-i18n="spatial.btn_ab">🔀 A/B: 3D HRTF ON</span>\n                </button>'),

    # View 6: Settings
    ('<span style="font-size: 0.68rem; color: var(--text-muted);">7 Idiomas Oficiais</span>',
     '<span style="font-size: 0.68rem; color: var(--text-muted);" data-i18n="settings.official_langs">7 Idiomas Oficiais</span>'),
    ('<div class="micro-label" style="margin-top: 10px; margin-bottom: 2px;">COMPORTAMENTO NO WINDOWS 11</div>',
     '<div class="micro-label" style="margin-top: 10px; margin-bottom: 2px;" data-i18n="settings.sys_title">COMPORTAMENTO NO WINDOWS 11</div>'),
    ('<span class="micro-label">ALERTAS & SAÚDE AUDITIVA</span>\n              <h2 class="section-title" style="font-size: 0.98rem;">Monitoramento & Notificações</h2>',
     '<span class="micro-label" data-i18n="settings.alerts_micro">ALERTAS & SAÚDE AUDITIVA</span>\n              <h2 class="section-title" data-i18n="settings.alerts_title" style="font-size: 0.98rem;">Monitoramento & Notificações</h2>'),
    ('<button class="btn" style="padding: 4px 10px; font-size: 0.72rem;" onclick="replaySplash()">\n                  ▶ Reproduzir\n                </button>',
     '<button class="btn" style="padding: 4px 10px; font-size: 0.72rem;" onclick="replaySplash()" data-i18n="settings.replay_btn">\n                  ▶ Reproduzir\n                </button>'),
    ('<div class="micro-label" style="margin-bottom: 4px;">SOBRE A SUÍTE</div>',
     '<div class="micro-label" style="margin-bottom: 4px;" data-i18n="settings.about_title">SOBRE A SUÍTE</div>'),
]

applied = 0
for target, repl in replacements:
    if target in content:
        content = content.replace(target, repl, 1)
        applied += 1
    else:
        print("WARNING: target not found:\n" + target[:60] + "...")

with open("index.html", "w", encoding="utf-8") as f:
    f.write(content)

print(f"Applied {applied}/{len(replacements)} replacements successfully to index.html.")

