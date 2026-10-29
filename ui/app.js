/* ==========================================================================
   HeadsetPlus Studio — Controlador Principal de Interface, Drivers & Automação
   Created by Matheus Veras • Source-Available Proprietary (Ver LICENSE.md)
   ========================================================================== */

let batTarget = { l: 0, r: 0, c: 0 };
let batCurrent = { l: 0, r: 0, c: 0 };
let batAnimRunning = false;

let currentNcMode = "ANC";
let currentAsmLevel = 10;
let currentVoiceFocus = false;

/* ==========================================================================
   NAVEGAÇÃO LATERAL, ACESSIBILIDADE DE TECLADO & VISIBILIDADE STANDBY
   ========================================================================== */
window.__hostWindowHidden = false;

function handleStandbyVisibilityChange(isVisible) {
  window.__hostWindowHidden = !isVisible;
  document.body.classList.toggle("page-hidden", !isVisible);
  if (!isVisible) {
    stopSpatialDemoPlayback(true);
    suspendAudioContextNow();
    stopHearingSafetyPoller();
  } else {
    startHearingSafetyPoller();
  }
}

window.onHostWindowVisibility = function (isVisible) {
  handleStandbyVisibilityChange(!!isVisible);
};

document.addEventListener("visibilitychange", () => {
  handleStandbyVisibilityChange(!document.hidden);
});

function switchView(viewId, idx, fromKeyboard = false) {
  document.querySelectorAll(".nav-btn[data-view]").forEach((btn) => {
    btn.classList.toggle("active", btn.getAttribute("data-view") === viewId);
  });

  const bar = document.getElementById("navActiveBar");
  if (bar) {
    if (typeof idx === "number" && idx >= 0 && idx < 5) {
      bar.style.opacity = "1";
      bar.style.transform = `translateY(${idx * 54}px)`;
    } else {
      bar.style.opacity = "0";
    }
  }

  document.querySelectorAll(".view-pane").forEach((pane) => {
    if (fromKeyboard) {
      pane.classList.add("instant-switch");
    } else {
      pane.classList.remove("instant-switch");
    }
    pane.classList.toggle("active", pane.id === `view-${viewId}`);
  });

  if (viewId !== "spatial" && typeof spatialDemoPlaying !== "undefined" && spatialDemoPlaying) {
    stopSpatialDemoPlayback(true);
  }
}
window.switchView = switchView;

window.addEventListener("keydown", (e) => {
  const activeEl = document.activeElement;
  if (activeEl && (activeEl.tagName === "INPUT" || activeEl.tagName === "SELECT" || activeEl.tagName === "TEXTAREA")) {
    if (e.key === "Escape") activeEl.blur();
    return;
  }
  if (
    activeEl &&
    (e.key === "Enter" || e.key === " ") &&
    (activeEl.getAttribute("role") === "switch" || activeEl.classList.contains("spatial-mode-card"))
  ) {
    e.preventDefault();
    activeEl.click();
    return;
  }
  if (e.key === "1") switchView("eq", 0, true);
  else if (e.key === "2") switchView("nc", 1, true);
  else if (e.key === "3") switchView("hw", 2, true);
  else if (e.key === "4") switchView("shield", 3, true);
  else if (e.key === "5") switchView("spatial", 4, true);
  else if (e.key === "6" || (e.ctrlKey && e.key === ",")) switchView("settings", 5, true);
  else if (e.key.toLowerCase() === "r") triggerReconnect();
});

/* ==========================================================================
   SELETOR DE DISPOSITIVOS MULTIMARCA (PLUGINS SONY V1 / V2 / UNIVERSAL WIN11)
   ========================================================================== */
let activeHeadset = { name: "WF-1000XM3", brand: "Sony", mac: "14:3F:A6:5D:DF:D5", protocol: "sony_mdr" };
let isMockModeActive = false;
let detectedHeadsetsList = [
  { name: "WF-1000XM3", brand: "Sony", mac: "14:3F:A6:5D:DF:D5", protocol: "sony_mdr" },
  { name: "WF-1000XM5", brand: "Sony", mac: "AC:80:0A:21:9F:10", protocol: "sony_mdr_v2" },
  { name: "realme Buds Air 5 Pro", brand: "realme", mac: "5D:9F:EF:71:D0:DD", protocol: "universal_windows" },
];

function toggleDeviceSelector(e) {
  e.stopPropagation();
  const wrap = document.getElementById("deviceSelectWrap");
  const menu = document.getElementById("deviceSelectMenu");
  if (!menu) return;
  const isOpen = menu.classList.contains("open");
  if (isOpen) {
    menu.classList.remove("open");
    wrap?.classList.remove("active");
    return;
  }

  // 1. Abertura Instantânea com latência ZERO (0 ms) usando o cache atual:
  renderDeviceSelectorItems();
  wrap?.classList.add("active");
  menu.classList.add("open");

  // 2. Consulta assíncrona em segundo plano para atualizar bateria/status sem bloquear o clique:
  if (window.pywebview && window.pywebview.api && window.pywebview.api.get_detected_headsets) {
    window.pywebview.api.get_detected_headsets(false).then((devices) => {
      if (devices && devices.length && menu.classList.contains("open")) {
        detectedHeadsetsList = devices;
        renderDeviceSelectorItems();
      }
    }).catch(() => {});
  }
}

const SIMULATED_SHOWCASE_MODELS = [
  { name: "Sony WH-1000XM5", brand: "Sony", desc: "Tandem V2 • LDAC Hi-Res • 8 Mics ANC" },
  { name: "Sony WF-1000XM4", brand: "Sony", desc: "Tandem V2 • TWS Case + L/R • LDAC" },
  { name: "Apple AirPods Pro", brand: "Apple", desc: "Universal Win11 • PnP • AutoEq Harman" },
  { name: "Apple AirPods Max", brand: "Apple", desc: "Universal Win11 • Over-Ear APO 64-bit" },
  { name: "Samsung Galaxy Buds2 Pro", brand: "Samsung", desc: "Universal Win11 • 24-bit Hi-Fi DSP" },
  { name: "Bose QuietComfort 45", brand: "Bose", desc: "Universal Win11 • Acoustic Noise Cancelling" },
  { name: "Sennheiser Momentum 4", brand: "Sennheiser", desc: "Universal Win11 • Audiophile 60h AutoEq" },
  { name: "realme Buds Air 5 Pro", brand: "realme", desc: "Universal Win11 • Coaxial Dual • 50dB ANC" }
];

function renderDeviceSelectorItems() {
  const menu = document.getElementById("deviceSelectMenu");
  if (!menu) return;
  const headerTxt = window.getTranslation ? window.getTranslation("header.device_select_header") : "DRIVERS & FONES PAREADOS:";
  let html = `<div style="font-size: 0.66rem; font-weight: 700; color: var(--sony-copper-bright); padding: 6px 10px; text-transform: uppercase;">${headerTxt}</div>`;
  if (!detectedHeadsetsList || detectedHeadsetsList.length === 0) {
    html += `<div style="font-size: 0.72rem; color: var(--text-muted); padding: 4px 10px 8px 10px;">Nenhum fone físico conectado no momento.</div>`;
  } else {
    detectedHeadsetsList.forEach((d) => {
      const isSel = !isMockModeActive && d.name === activeHeadset.name;
      const safeD = JSON.stringify(d).replace(/'/g, "&apos;");
      const batTag = typeof d.battery_pct === "number" ? ` • ${d.battery_pct}%` : "";
      const protoBadge = d.protocol === "sony_mdr_v2" ? "V2" : (d.protocol === "sony_mdr" ? "MDR" : "APO");
      html += `
        <div class="popover-item ${isSel ? "selected" : ""}" onclick='selectActiveHeadset(${safeD})'>
          <div style="display: flex; flex-direction: column; gap: 2px;">
            <div style="font-weight: 600; font-size: 0.79rem;">${d.name}</div>
            <div style="font-size: 0.64rem; color: var(--text-muted); font-family: monospace;">${d.mac || "Windows PnP"}${batTag}</div>
          </div>
          <span class="device-item-pill">${d.brand || protoBadge}</span>
        </div>
      `;
    });
  }

  const simHeaderTxt = window.getTranslation ? window.getTranslation("header.sim_section_header") : "🧪 LAB DE SIMULAÇÃO (TESTAR OUTROS FONES):";
  html += `<div style="border-top: 1px solid rgba(255,255,255,0.08); margin: 6px 4px 4px 4px;"></div>`;
  html += `<div style="font-size: 0.64rem; font-weight: 700; color: var(--ghub-cyan); padding: 4px 10px; text-transform: uppercase;">${simHeaderTxt}</div>`;

  SIMULATED_SHOWCASE_MODELS.forEach((sim) => {
    const isSel = isMockModeActive && activeHeadset.name.includes(sim.name);
    html += `
      <div class="popover-item ${isSel ? "selected" : ""}" onclick="simulateModelFromDropdown('${sim.name}')">
        <div style="display: flex; flex-direction: column; gap: 2px;">
          <div style="font-weight: 600; font-size: 0.77rem; color: #fff;">${sim.name}</div>
          <div style="font-size: 0.62rem; color: var(--text-muted);">${sim.desc}</div>
        </div>
        <span class="device-item-pill" style="color: var(--ghub-cyan); border-color: rgba(0,245,212,0.3);">${sim.brand}</span>
      </div>
    `;
  });

  menu.innerHTML = html;
}

function simulateModelFromDropdown(modelName) {
  document.getElementById("deviceSelectWrap")?.classList.remove("active");
  document.getElementById("deviceSelectMenu")?.classList.remove("open");
  if (window.pywebview && window.pywebview.api && window.pywebview.api.simulate_headset_model) {
    window.pywebview.api.simulate_headset_model(modelName).then((res) => {
      isMockModeActive = true;
      activeHeadset = { name: res.name, brand: res.brand, protocol: res.protocol, mac: "AA:BB:CC:DD:EE:FF" };
      document.getElementById("modelTitle").textContent = `${res.name} (Simulado)`;
      document.getElementById("brandPill").textContent = `${res.brand.toUpperCase()} AUDIO`;
      renderDeviceSelectorItems();
      const mockToggle = document.getElementById("chkMockMode");
      if (mockToggle) mockToggle.checked = true;
    });
  }
}

function activateMockFromDropdown() {
  document.getElementById("deviceSelectWrap")?.classList.remove("active");
  document.getElementById("deviceSelectMenu")?.classList.remove("open");
  setMockModeUI(!isMockModeActive);
}

function selectActiveHeadset(dev) {
  isMockModeActive = false;
  const mockToggle = document.getElementById("chkMockMode");
  if (mockToggle) mockToggle.checked = false;
  activeHeadset = dev;
  document.getElementById("modelTitle").textContent = dev.name;
  document.getElementById("brandPill").textContent = `${(dev.brand || "BT").toUpperCase()} AUDIO`;
  document.getElementById("deviceSelectWrap")?.classList.remove("active");
  document.getElementById("deviceSelectMenu")?.classList.remove("open");
  if (dev.mac) {
    const inpMac = document.getElementById("inpMac");
    if (inpMac) inpMac.value = dev.mac;
  }

  if (window.pywebview && window.pywebview.api && window.pywebview.api.select_headset_device) {
    window.pywebview.api.select_headset_device(dev).then((info) => {
      const pLabel = info.protocol === "sony_mdr_v2"
        ? "Sony Tandem V2"
        : (info.protocol === "sony_mdr" ? "Sony MDR V1" : "Windows 11 PnP + APO Global");
      showToast(`Driver ativo: ${info.name} [${pLabel}]`, "🎧");
    });
  } else {
    showToast(`Dispositivo Ativo: ${dev.name}`, "🎧");
  }

  if (dev.name.toLowerCase().includes("realme")) {
    eqTarget = [1, -2, 0, 3, 2, 1];
    startEqSpring();
    setActivePresetUI("AutoEq: realme Buds Air 5 Pro");
  }
}

window.addEventListener("pointerdown", (e) => {
  const dWrap = document.getElementById("deviceSelectWrap");
  const dMenu = document.getElementById("deviceSelectMenu");
  if (dWrap && dMenu && !dWrap.contains(e.target)) {
    dWrap.classList.remove("active");
    dMenu.classList.remove("open");
  }
});

function scanPairedHeadsets() {
  const listEl = document.getElementById("detectedHeadsetsList");
  if (!listEl) return;
  listEl.style.display = "block";
  listEl.innerHTML = "<div style='font-size: 0.75rem; color: var(--text-muted);'>Escaneando dispositivos Bluetooth e bateria PnP no Windows 11...</div>";
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.get_detected_headsets(true).then((devices) => {
      if (!devices || devices.length === 0) {
        listEl.innerHTML = "<div style='font-size: 0.75rem; color: var(--text-secondary);'>Nenhum fone Bluetooth pareado encontrado.</div>";
        return;
      }
      detectedHeadsetsList = devices;
      let html = "<div style='font-size: 0.70rem; font-weight: 700; color: var(--sony-copper-bright); margin-bottom: 6px; text-transform: uppercase;'>Clique em qualquer fone para ativar seu driver:</div><div style='display: flex; flex-direction: column; gap: 6px;'>";
      devices.forEach((dev) => {
        if (dev.name) {
          const safeD = JSON.stringify(dev).replace(/'/g, "&apos;");
          const batStr = typeof dev.battery_pct === "number" ? `<span style="color: var(--emerald); font-weight: 700; margin-right: 8px;">🔋 ${dev.battery_pct}%</span>` : "";
          html += `<div style="display: flex; justify-content: space-between; align-items: center; background: rgba(255,255,255,0.035); padding: 6px 10px; border-radius: 7px; cursor: pointer;" onclick='selectActiveHeadset(${safeD})'>
            <div>
              <span style="font-weight: 600; font-size: 0.79rem; color: var(--text-primary);">${dev.name}</span>
              <span style="font-size: 0.69rem; color: var(--text-muted); margin-left: 6px;">[${dev.brand} • ${dev.protocol}]</span>
            </div>
            <div>
              ${batStr}
              <span style="font-size: 0.68rem; font-family: monospace; color: var(--ghub-cyan);">${dev.mac || "PnP"}</span>
            </div>
          </div>`;
        }
      });
      html += "</div>";
      listEl.innerHTML = html;
    });
  }
}

/* ==========================================================================
   MOTOR DSP GLOBAL WINDOWS 11 (EQUALIZER APO) & AUTOMAÇÃO DE COMBOS POR APP
   ========================================================================== */
let apoGlobalEnabled = true;
let automationRules = [
  { exe: "cs2.exe", label: "Counter-Strike 2", icon: "🎮", eq_preset: "Gaming FPS (Passos)", nc_mode: "ANC", asm_level: 10, focus_voice: false, spatial_mode: "esports" },
  { exe: "valorant.exe", label: "Valorant", icon: "🎮", eq_preset: "Gaming FPS (Passos)", nc_mode: "ANC", asm_level: 10, focus_voice: false, spatial_mode: "esports" },
  { exe: "spotify.exe", label: "Spotify", icon: "🎵", eq_preset: "Audiófilo (Comunidade)", nc_mode: "ANC", asm_level: 10, focus_voice: false, spatial_mode: "hifi" },
  { exe: "discord.exe", label: "Discord (Voz + Transparência)", icon: "🎙️", eq_preset: "Voz & Podcast", nc_mode: "Ambiente", asm_level: 14, focus_voice: true, spatial_mode: "nearfield" },
  { exe: "vlc.exe", label: "VLC Media Player", icon: "🎬", eq_preset: "Cinema Sub-Bass", nc_mode: "ANC", asm_level: 10, focus_voice: false, spatial_mode: "hifi" },
];

function renderApoStatusUI(apo) {
  if (!apo) return;
  apoGlobalEnabled = !!apo.enabled;
  document.getElementById("swGlobalApo")?.classList.toggle("on", apoGlobalEnabled);
  const pill = document.getElementById("apoStatusPill");
  const sub = document.getElementById("lblApoSubStatus");
  if (pill) {
    if (apo.apo_installed && apo.apo_linked) {
      pill.classList.remove("local");
      pill.textContent = "APO Vinculado Ao Vivo";
    } else if (apo.apo_installed) {
      pill.classList.add("local");
      pill.textContent = "APO Detectado (Clique em Vincular)";
    } else {
      pill.classList.add("local");
      pill.textContent = "Script APO Ativo (apo_dsp/)";
    }
  }
  if (sub) {
    sub.textContent = apo.apo_installed
      ? "Processando 6 bandas Biquad + Crossfeed Linkwitz em todo o áudio do Windows 11."
      : "Exportando matriz DSP em tempo real em apo_dsp/sony_sound_connect_dsp.txt.";
  }
}

function toggleGlobalApoSwitch() {
  const sw = document.getElementById("swGlobalApo");
  apoGlobalEnabled = sw.classList.toggle("on");
  if (window.pywebview && window.pywebview.api && window.pywebview.api.set_apo_enabled) {
    window.pywebview.api.set_apo_enabled(apoGlobalEnabled).then(renderApoStatusUI);
  }
  showToast(`Motor DSP Global Windows 11 ${apoGlobalEnabled ? "ativado" : "em bypass (0 dB)"}`, "🎛️");
}

function linkEqualizerApoClick() {
  if (window.pywebview && window.pywebview.api && window.pywebview.api.link_equalizer_apo) {
    window.pywebview.api.link_equalizer_apo().then((res) => {
      if (window.pywebview.api.get_apo_status) {
        window.pywebview.api.get_apo_status().then(renderApoStatusUI);
      }
      showToast(res.message || "Filtro Equalizer APO sincronizado!", "🔗");
    });
  } else {
    showToast("Script sony_sound_connect_dsp.txt pronto para Equalizer APO!", "🔗");
  }
}

function toggleAutoProfileSwitch() {
  const sw = document.getElementById("swAutoProfile");
  const isOn = sw.classList.toggle("on");
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.set_auto_profile_enabled(isOn);
  }
}

function renderAutomationRulesList() {
  const box = document.getElementById("automationRulesList");
  if (!box) return;
  if (!automationRules || !automationRules.length) {
    box.innerHTML = "<div style='font-size: 0.73rem; color: var(--text-muted);'>Nenhuma regra cadastrada.</div>";
    return;
  }

  let html = "";
  automationRules.forEach((r) => {
    const safeExe = String(r.exe || "").replace(/'/g, "");
    const safeRule = JSON.stringify(r).replace(/'/g, "&apos;");
    const ncLabel = r.nc_mode === "Ambiente" ? `Ambiente ${r.asm_level || 14}${r.focus_voice ? " • Voz" : ""}` : r.nc_mode;
    const spLabel = (r.spatial_mode || "nearfield").toUpperCase();
    html += `
      <div class="auto-rule-item" onclick='loadRuleIntoEditor(${safeRule})' title="Clique para editar ${safeExe}">
        <div style="min-width: 0;">
          <div style="font-size: 0.76rem; font-weight: 700; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
            ${r.icon || "⚡"} ${safeExe}
          </div>
          <div class="auto-rule-tags">
            <span class="auto-tag">${r.eq_preset}</span>
            <span class="auto-tag nc">${ncLabel}</span>
            <span class="auto-tag sp">3D ${spLabel}</span>
          </div>
        </div>
        <button class="auto-del-btn" onclick="event.stopPropagation(); deleteAutomationRuleUI('${safeExe}')" title="Remover regra">✕</button>
      </div>
    `;
  });
  box.innerHTML = html;
}

function loadRuleIntoEditor(rule) {
  if (!rule) return;
  const inp = document.getElementById("inpAutoExe");
  const cmbEq = document.getElementById("cmbAutoEq");
  const cmbNc = document.getElementById("cmbAutoNc");
  const cmbSp = document.getElementById("cmbAutoSpatial");
  if (inp) inp.value = rule.exe || "";
  if (cmbEq) cmbEq.value = rule.eq_preset || "Gaming FPS (Passos)";
  if (cmbNc) cmbNc.value = rule.nc_mode || "ANC";
  if (cmbSp) cmbSp.value = rule.spatial_mode || "nearfield";
}

function saveAutomationRuleUI() {
  const inp = document.getElementById("inpAutoExe");
  const rawExe = (inp?.value || "").trim().toLowerCase();
  if (!rawExe) {
    showToast("Informe o executável (ex: discord.exe ou cs2.exe)", "ℹ️");
    return;
  }
  const exe = rawExe.endsWith(".exe") ? rawExe : `${rawExe}.exe`;
  const eq_preset = document.getElementById("cmbAutoEq")?.value || "Gaming FPS (Passos)";
  const nc_mode = document.getElementById("cmbAutoNc")?.value || "ANC";
  const spatial_mode = document.getElementById("cmbAutoSpatial")?.value || "nearfield";

  const isVoiceApp = nc_mode === "Ambiente" || eq_preset === "Voz & Podcast";
  const rule = {
    exe,
    label: exe.replace(".exe", "").toUpperCase(),
    icon: eq_preset.includes("FPS") ? "🎮" : (isVoiceApp ? "🎙️" : (eq_preset.includes("Cinema") ? "🎬" : "🎵")),
    eq_preset,
    nc_mode,
    asm_level: isVoiceApp ? 14 : 10,
    focus_voice: isVoiceApp,
    spatial_mode,
  };

  if (window.pywebview && window.pywebview.api && window.pywebview.api.save_automation_rule) {
    window.pywebview.api.save_automation_rule(rule).then((updated) => {
      automationRules = updated || automationRules;
      renderAutomationRulesList();
    });
  } else {
    const idx = automationRules.findIndex((r) => r.exe === exe);
    if (idx >= 0) automationRules[idx] = rule;
    else automationRules.unshift(rule);
    renderAutomationRulesList();
  }
  if (inp) inp.value = "";
  playCommitChime();
  showToast(`Combo salvo para ${exe}: ${eq_preset} + ${nc_mode}!`, "⚡");
}

function deleteAutomationRuleUI(exeName) {
  if (window.pywebview && window.pywebview.api && window.pywebview.api.delete_automation_rule) {
    window.pywebview.api.delete_automation_rule(exeName).then((updated) => {
      automationRules = updated || [];
      renderAutomationRulesList();
    });
  } else {
    automationRules = automationRules.filter((r) => r.exe !== exeName);
    renderAutomationRulesList();
  }
  showToast(`Regra removida: ${exeName}`, "🗑️");
}

function resetAutomationRulesUI() {
  if (window.pywebview && window.pywebview.api && window.pywebview.api.reset_automation_rules) {
    window.pywebview.api.reset_automation_rules().then((updated) => {
      automationRules = updated || [];
      renderAutomationRulesList();
    });
  }
  showToast("Combos de automação restaurados para o padrão!", "↺");
}

/* ==========================================================================
   CONTROLE DE RUÍDO (ANC / VENTO / AMBIENTE) & HALO ISOLADO NA GPU
   ========================================================================== */
let lastAppliedHaloMode = "";

function updateHaloByMode(mode) {
  const badge = document.getElementById("modeBadge");
  if (badge) badge.textContent = mode;
  if (mode === lastAppliedHaloMode) return;
  lastAppliedHaloMode = mode;

  const haloEl = document.getElementById("ambientHaloLayer");
  if (!haloEl) return;
  if (mode === "ANC") {
    haloEl.style.setProperty("--halo-color", "rgba(0, 229, 255, 0.16)");
  } else if (mode === "Vento") {
    haloEl.style.setProperty("--halo-color", "rgba(56, 189, 248, 0.19)");
  } else if (mode === "Ambiente") {
    haloEl.style.setProperty("--halo-color", "rgba(197, 160, 89, 0.21)");
  } else {
    haloEl.style.setProperty("--halo-color", "rgba(148, 163, 184, 0.07)");
  }
}

function selectNcMode(mode) {
  currentNcMode = mode;
  ["ANC", "Vento", "Ambiente", "Desligado"].forEach((m) => {
    const card = document.getElementById(`ncCard-${m}`);
    if (card) card.classList.toggle("active", m === mode);
  });
  const asmBox = document.querySelector(".asm-scrubber-box");
  if (asmBox) asmBox.classList.toggle("inactive", mode !== "Ambiente");
  updateHaloByMode(mode);
  commitNcSettings();
  showToast(`Controle Acústico: ${mode}`, "🎧");
}

function onAsmSliderInput(val) {
  currentAsmLevel = parseInt(val, 10);
  const el = document.getElementById("lblAsmVal");
  if (el) el.textContent = currentAsmLevel;
}

function toggleVoiceFocusClick() {
  currentVoiceFocus = !currentVoiceFocus;
  document.getElementById("toggleVoiceFocus")?.classList.toggle("on", currentVoiceFocus);
  commitNcSettings();
}

function commitNcSettings() {
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.set_nc_asm(currentNcMode, currentAsmLevel, currentVoiceFocus);
  }
}

/* ==========================================================================
   HARDWARE, SENSORES TOUCH, MOCK HARNESS & HOLD-TO-CONFIRM POWER OFF
   ========================================================================== */
function setMockModeUI(enabled) {
  isMockModeActive = !!enabled;
  document.getElementById("swMockMode")?.classList.toggle("on", isMockModeActive);
  if (window.pywebview && window.pywebview.api && window.pywebview.api.set_mock_mode) {
    window.pywebview.api.set_mock_mode(isMockModeActive);
  } else {
    showToast(
      isMockModeActive ? "Simulador Virtual Mock ativado!" : "Modo Hardware Bluetooth Real ativado.",
      isMockModeActive ? "🤖" : "📡"
    );
  }
}

function toggleMockModeClick() {
  setMockModeUI(!isMockModeActive);
}

function onConnModeChange(val) {
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.set_connection_mode(val === "Prioridade na Conexão Estável");
  }
  showToast(val, "📡");
}

function toggleDseeClick() {
  const el = document.getElementById("swDsee");
  const enabled = !el.classList.contains("on");
  el.classList.toggle("on", enabled);
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.set_dsee_hx(enabled);
  }
  showToast(`DSEE HX ${enabled ? "Ativado" : "Desativado"}`, "🎵");
}

function toggleWearingClick() {
  const el = document.getElementById("swWearing");
  const enabled = !el.classList.contains("on");
  el.classList.toggle("on", enabled);
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.set_wearing_pause(enabled);
  }
  showToast(`Sensor de Pausa ${enabled ? "Ativado" : "Desativado"}`, "👂");
}

function onAutoOffChange(val) {
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.set_auto_power_off(val);
  }
  showToast(`Auto-Off: ${val}`, "⏱️");
}

function onTouchChange() {
  const l = document.getElementById("cmbTouchL").value;
  const r = document.getElementById("cmbTouchR").value;
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.set_touch_sensors(l, r);
  }
  showToast(`Touch atualizado (L: ${l.split(" ").pop()} | R: ${r.split(" ").pop()})`, "👆");
}

function saveMacAddress() {
  const mac = document.getElementById("inpMac").value.trim();
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.update_mac_address(mac);
  }
  showToast(`Endereço MAC salvo: ${mac}`, "🔗");
}

let holdTimer = null;
function startHoldPowerOff() {
  const btn = document.getElementById("btnHoldPowerOff");
  btn.classList.add("holding");
  document.getElementById("lblHoldPowerOff").textContent = "⏻ Mantenha pressionado...";
  if (holdTimer) clearTimeout(holdTimer);
  holdTimer = setTimeout(() => {
    btn.classList.remove("holding");
    document.getElementById("lblHoldPowerOff").textContent = "⏻ Fones Desligados!";
    if (window.pywebview && window.pywebview.api) {
      window.pywebview.api.power_off_headphones();
    }
    showToast("Comando de desligamento enviado aos fones", "⏻");
  }, 1400);
}

function cancelHoldPowerOff() {
  const btn = document.getElementById("btnHoldPowerOff");
  if (!btn) return;
  btn.classList.remove("holding");
  document.getElementById("lblHoldPowerOff").textContent = "⏻ Segure 1.4s para Desligar os Fones";
  if (holdTimer) {
    clearTimeout(holdTimer);
    holdTimer = null;
  }
}

function runWindowsShieldFix() {
  showToast("Aplicando Blindagem Estéreo A2DP no Windows 11...", "🔒");
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.reapply_windows_audio_fix();
  }
}

function cycleBluetoothStack() {
  showToast("Reiniciando pilha Bluetooth do fone...", "🔄");
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.cycle_bluetooth();
  }
}

function triggerReconnect() {
  const btn = document.getElementById("btnSync");
  if (btn) {
    const syncTxt = window.getTranslation ? window.getTranslation("header.connecting") : "Conectando...";
    btn.innerHTML = `<span>⏳ ${syncTxt}</span>`;
  }
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.reconnect();
  }
  setTimeout(() => {
    const b = document.getElementById("btnSync");
    const syncBtnLabel = window.getTranslation ? window.getTranslation("header.sync_btn") : "🔄 Sincronizar";
    if (b && b.innerHTML.includes("⏳")) {
      b.innerHTML = `<span>${syncBtnLabel}</span>`;
    }
  }, 2800);
}

function minimizeToTray() {
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.hide_to_tray();
  }
}

function triggerNativeDesktopOverlay() {
  if (window.pywebview && window.pywebview.api && window.pywebview.api.trigger_desktop_ios_overlay) {
    window.pywebview.api.trigger_desktop_ios_overlay();
    showToast("Overlay Flutuante Nativo Windows 11 exibido (Zero Focus-Steal)!", "🪟");
  } else {
    window.showIosBatteryPopup();
  }
}

/* ==========================================================================
   ANIMAÇÃO DOS ANÉIS DE BATERIA, POP-UP IOS & RECEPÇÃO DE ESTADO DO PYTHON
   ========================================================================== */
const CIRCUMFERENCE = 144.5;

function renderBatteryRingsImmediate() {
  [
    { key: "l", ring: "ringLeft", val: "valLeft" },
    { key: "c", ring: "ringCase", val: "valCase" },
    { key: "r", ring: "ringRight", val: "valRight" },
  ].forEach(({ key, ring, val }) => {
    const pct = Math.round(batCurrent[key]);
    const ringEl = document.getElementById(ring);
    const valEl = document.getElementById(val);
    if (ringEl && valEl) {
      const offset = CIRCUMFERENCE - (pct / 100) * CIRCUMFERENCE;
      ringEl.style.strokeDashoffset = offset.toFixed(1);
      ringEl.style.stroke = pct <= 0 ? "rgba(255,255,255,0.08)" : (pct <= 20 ? "var(--danger)" : (key === "c" ? "var(--sony-copper-bright)" : "var(--emerald)"));
      valEl.textContent = pct > 0 ? `${pct}%` : "--%";
    }
  });
}

function animateBatteries() {
  if (document.hidden || window.__hostWindowHidden) {
    batCurrent.l = batTarget.l;
    batCurrent.c = batTarget.c;
    batCurrent.r = batTarget.r;
    batAnimRunning = false;
    renderBatteryRingsImmediate();
    return;
  }
  if (batAnimRunning) return;
  batAnimRunning = true;

  function tick() {
    if (document.hidden || window.__hostWindowHidden) {
      batCurrent.l = batTarget.l;
      batCurrent.c = batTarget.c;
      batCurrent.r = batTarget.r;
      batAnimRunning = false;
      renderBatteryRingsImmediate();
      return;
    }
    let moving = false;
    ["l", "c", "r"].forEach((key) => {
      const diff = batTarget[key] - batCurrent[key];
      if (Math.abs(diff) > 0.35) {
        batCurrent[key] += diff * 0.18;
        moving = true;
      } else {
        batCurrent[key] = batTarget[key];
      }
    });
    renderBatteryRingsImmediate();

    if (moving) {
      requestAnimationFrame(tick);
    } else {
      batAnimRunning = false;
    }
  }

  requestAnimationFrame(tick);
}

const IOS_CIRCUMFERENCE = 113.1;
let iosPopupTimer = null;
let wasConnectedBefore = false;

function setIosGauge(ringId, valId, pct, isCase) {
  const ring = document.getElementById(ringId);
  const val = document.getElementById(valId);
  if (!ring || !val) return;
  const clamped = Math.max(0, Math.min(100, Math.round(pct || 0)));
  const offset = IOS_CIRCUMFERENCE - (clamped / 100) * IOS_CIRCUMFERENCE;
  ring.style.strokeDashoffset = offset.toFixed(1);
  if (clamped <= 20) {
    ring.style.stroke = "var(--danger)";
  } else if (isCase) {
    ring.style.stroke = "var(--sony-copper-bright)";
  } else {
    ring.style.stroke = "var(--emerald)";
  }
  val.textContent = clamped > 0 ? `${clamped}%` : "--%";
}

function syncIosPopupUI(st) {
  if (!st) return;
  if (st.model) {
    const title = document.getElementById("iosPopupTitle");
    if (title) title.textContent = st.model;
  }
  setIosGauge("iosRingL", "iosValL", st.bat_l, false);
  setIosGauge("iosRingCase", "iosValCase", st.bat_case, true);
  setIosGauge("iosRingR", "iosValR", st.bat_r, false);

  const chgL = document.getElementById("iosChgL");
  const chgC = document.getElementById("iosChgCase");
  const chgR = document.getElementById("iosChgR");
  if (chgL) chgL.textContent = st.bat_l_charging ? "⚡ CARREGANDO" : "";
  if (chgC) chgC.textContent = st.bat_case_charging ? "⚡ CARREGANDO" : "";
  if (chgR) chgR.textContent = st.bat_r_charging ? "⚡ CARREGANDO" : "";
}

window.showIosBatteryPopup = function () {
  triggerNativeDesktopOverlay();
};

window.dismissIosBatteryPopup = function () {
  document.getElementById("iosBatteryPopup")?.classList.remove("active");
  if (iosPopupTimer) {
    clearTimeout(iosPopupTimer);
    iosPopupTimer = null;
  }
};

window.updateFromPythonState = function (st) {
  const btnSync = document.getElementById("btnSync");
  const syncLabel = window.getTranslation ? window.getTranslation("header.sync_btn") : "🔄 Sincronizar";
  if (btnSync) btnSync.innerHTML = `<span>${syncLabel}</span>`;
  const cleanModel = String(st.model || "WF-1000XM3").replace(/\s*\(Mock\)/gi, "").trim();
  document.getElementById("modelTitle").textContent = cleanModel || "WF-1000XM3";
  document.getElementById("fwBadge").textContent = String(st.fw_version || "3.1.2").startsWith("Win")
    ? st.fw_version
    : "v" + (st.fw_version || "3.1.2");
  document.getElementById("codecBadge").textContent = st.codec || "AAC";
  if (st.mac) document.getElementById("inpMac").value = st.mac;

  if (typeof st.mock_mode === "boolean") {
    isMockModeActive = st.mock_mode;
    document.getElementById("swMockMode")?.classList.toggle("on", isMockModeActive);
  }
  const brandUpper = String(st.brand || "SONY").toUpperCase();
  const bPill = document.getElementById("brandPill");
  if (bPill) bPill.textContent = `${brandUpper} AUDIO`;

  const pill = document.getElementById("connPill");
  const connTxt = document.getElementById("connText");
  if (st.connected) {
    pill.classList.remove("disconnected");
    connTxt.textContent = window.getTranslation ? window.getTranslation("header.connected") : "Conectado";
  } else {
    pill.classList.add("disconnected");
    connTxt.textContent = window.getTranslation ? window.getTranslation("header.disconnected") : "Desconectado";
  }

  if (!st.connected) {
    batTarget.l = 0;
    batTarget.r = 0;
    batTarget.c = 0;
    batCurrent.l = 0;
    batCurrent.r = 0;
    batCurrent.c = 0;
    renderBatteryRingsImmediate();
  } else {
    batTarget.l = st.bat_l || 0;
    batTarget.r = st.bat_r || 0;
    batTarget.c = st.bat_case || 0;
    animateBatteries();
  }
  const chgLabel = window.getTranslation ? window.getTranslation("hero.charging") : "Carregando";
  document.getElementById("chgLeft").textContent = (st.connected && st.bat_l_charging) ? `⚡ ${chgLabel.toUpperCase()}` : "";
  document.getElementById("chgRight").textContent = (st.connected && st.bat_r_charging) ? `⚡ ${chgLabel.toUpperCase()}` : "";
  document.getElementById("chgCase").textContent = (st.connected && st.bat_case_charging) ? `⚡ ${chgLabel.toUpperCase()}` : "";

  currentNcMode = st.nc_mode || "ANC";
  ["ANC", "Vento", "Ambiente", "Desligado"].forEach((m) => {
    const card = document.getElementById(`ncCard-${m}`);
    if (card) card.classList.toggle("active", m === currentNcMode);
  });
  const asmBox = document.querySelector(".asm-scrubber-box");
  if (asmBox) asmBox.classList.toggle("inactive", currentNcMode !== "Ambiente");
  updateHaloByMode(currentNcMode);

  currentAsmLevel = st.asm_level || 10;
  document.getElementById("sliderAsm").value = currentAsmLevel;
  document.getElementById("lblAsmVal").textContent = currentAsmLevel;

  currentVoiceFocus = !!st.focus_on_voice;
  document.getElementById("toggleVoiceFocus")?.classList.toggle("on", currentVoiceFocus);

  if (st.eq_preset && st.eq_preset !== "Desligado (Off)") {
    setActivePresetUI(st.eq_preset);
  }
  if (typeof st.clear_bass === "number" && Array.isArray(st.eq_bands) && draggingIdx === -1) {
    const isAllZero = st.clear_bass === 0 && st.eq_bands.every((b) => b === 0);
    if (!isAllZero || st.eq_preset === "Desligado (Off)") {
      eqTarget = [st.clear_bass, ...st.eq_bands];
      startEqSpring();
    }
  }

  if (st.conn_mode) document.getElementById("cmbConnMode").value = st.conn_mode;
  document.getElementById("swDsee")?.classList.toggle("on", !!st.dsee_hx);
  document.getElementById("swWearing")?.classList.toggle("on", !!st.wearing_pause);
  if (st.auto_off) document.getElementById("cmbAutoOff").value = st.auto_off;
  if (st.touch_l) document.getElementById("cmbTouchL").value = st.touch_l;
  if (st.touch_r) document.getElementById("cmbTouchR").value = st.touch_r;

  wasConnectedBefore = !!st.connected;
};

window.setStatusText = function (_msg) {};

window.setNanoAssets = function (assets) {
  if (assets.l) {
    document.getElementById("imgLeft").src = assets.l;
    const pL = document.getElementById("iosPopupImgL");
    if (pL) pL.src = assets.l;
  }
  if (assets.r) {
    document.getElementById("imgRight").src = assets.r;
    const pR = document.getElementById("iosPopupImgR");
    if (pR) pR.src = assets.r;
  }
  if (assets.c) {
    document.getElementById("imgCase").src = assets.c;
    const pC = document.getElementById("iosPopupImgCase");
    if (pC) pC.src = assets.c;
  }
  if (assets.icon) {
    const brandIcon = document.getElementById("imgBrandIcon");
    if (brandIcon) brandIcon.src = assets.icon;
    const splashIcon = document.getElementById("splashAppIcon");
    if (splashIcon) splashIcon.src = assets.icon;
  }
};

/* ==========================================================================
   TRANSIÇÃO CINEMATOGRÁFICA APPLE TV (SPLASH SCREEN) & SONNER TOAST
   ========================================================================== */
let splashDismissed = false;
let splashTimer = null;

window.dismissSplash = function () {
  if (splashDismissed) return;
  splashDismissed = true;
  if (splashTimer) clearTimeout(splashTimer);

  const splash = document.getElementById("splashScreen");
  if (!splash) return;

  splash.classList.add("dismissing");
  document.getElementById("appLayout")?.classList.add("app-revealing");

  setTimeout(() => {
    if (splash && splash.parentNode) {
      splash.style.display = "none";
    }
  }, 720);
};

window.startSplashTimer = function () {
  if (splashDismissed) return;
  if (splashTimer) clearTimeout(splashTimer);
  splashTimer = setTimeout(() => {
    window.dismissSplash();
  }, 2600);
};

window.addEventListener("load", () => {
  setTimeout(() => {
    if (!splashTimer && !splashDismissed) {
      window.startSplashTimer();
    }
  }, 800);
});

window.replaySplash = function () {
  const splash = document.getElementById("splashScreen");
  if (splash) {
    splash.style.display = "flex";
    splash.classList.remove("dismissing");
    splashDismissed = false;
    document.getElementById("appLayout")?.classList.remove("app-revealing");
    window.startSplashTimer();
  }
};

window.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    window.dismissIosBatteryPopup();
    document.getElementById("deviceSelectMenu")?.classList.remove("open");
    document.getElementById("presetPopoverMenu")?.classList.remove("open");
  }
  if (!splashDismissed && (e.key === " " || e.key === "Enter" || e.key === "Escape")) {
    window.dismissSplash();
  }
});

let toastTimeout = null;
window.showToast = function (text, icon = "✨") {
  const el = document.getElementById("sonnerToast");
  if (!el) return;
  document.getElementById("toastIcon").textContent = icon;
  document.getElementById("toastText").textContent = text;
  el.classList.add("visible");
  if (toastTimeout) clearTimeout(toastTimeout);
  toastTimeout = setTimeout(() => {
    el.classList.remove("visible");
  }, 2400);
};

window.addEventListener("pywebviewready", () => {
  if (window.pywebview && window.pywebview.api && window.pywebview.api.get_runtime_bootstrap) {
    window.pywebview.api.get_runtime_bootstrap().then((boot) => {
      if (!boot) return;
      if (typeof boot.mock_mode === "boolean") {
        isMockModeActive = boot.mock_mode;
        document.getElementById("swMockMode")?.classList.toggle("on", isMockModeActive);
      }
      if (typeof boot.auto_profiles_enabled === "boolean") {
        document.getElementById("swAutoProfile")?.classList.toggle("on", boot.auto_profiles_enabled);
      }
      if (boot.active_device) {
        activeHeadset = boot.active_device;
      }
      if (boot.apo_status) {
        renderApoStatusUI(boot.apo_status);
      }
      if (Array.isArray(boot.automation_rules) && boot.automation_rules.length) {
        automationRules = boot.automation_rules;
        renderAutomationRulesList();
      }
      if (Array.isArray(boot.biometric_profiles) && boot.biometric_profiles.length) {
        biometricProfiles = boot.biometric_profiles;
        selectedBioProfileId = biometricProfiles[0].id;
        renderBiometricProfileSelect();
        onSelectBioProfile(selectedBioProfileId);
      }
      if (boot.saved_custom_eq) {
        const cb = typeof boot.saved_custom_eq.clear_bass === "number" ? boot.saved_custom_eq.clear_bass : 3;
        const bds = Array.isArray(boot.saved_custom_eq.bands) ? boot.saved_custom_eq.bands : [-1, 2, 4, 4, 2];
        const pName = boot.active_eq_preset || "Audiófilo (Comunidade)";
        window.applySavedEqToUI && window.applySavedEqToUI(pName, cb, bds);
      }
      const syncAccent = localStorage.getItem("sony_sync_win_accent") === "true";
      document.getElementById("swWinAccentSync")?.classList.toggle("on", syncAccent);
      if (typeof boot.run_at_startup === "boolean") {
        document.getElementById("swStartup")?.classList.toggle("on", boot.run_at_startup);
      }
      const closePref = localStorage.getItem("sony_close_to_tray");
      if (closePref !== null) {
        document.getElementById("swCloseToTray")?.classList.toggle("on", closePref === "true");
      } else if (typeof boot.close_to_tray === "boolean") {
        document.getElementById("swCloseToTray")?.classList.toggle("on", boot.close_to_tray);
      }
      const overlayPref = localStorage.getItem("sony_show_overlay");
      if (overlayPref !== null) {
        document.getElementById("swOverlayPref")?.classList.toggle("on", overlayPref === "true");
      }
      const lowBatPref = localStorage.getItem("sony_low_bat_toast");
      if (lowBatPref !== null) {
        document.getElementById("swLowBatToast")?.classList.toggle("on", lowBatPref === "true");
      }
      const splPref = localStorage.getItem("sony_spl_dosimeter");
      if (splPref !== null) {
        document.getElementById("swSplDosimeter")?.classList.toggle("on", splPref === "true");
      }
      if (boot.language) {
        window.__systemLanguage = boot.system_language || boot.language;
        const savedLang = localStorage.getItem("sony_lang");
        const activeLang = savedLang || boot.language;
        if (typeof setAppLanguage === "function") {
          setAppLanguage(activeLang, true);
        }
      } else if (typeof setAppLanguage === "function" && typeof currentAppLanguage === "string") {
        setAppLanguage(currentAppLanguage, true);
      }
    });
  }
});

/* ==========================================================================
   SINCRONIZAÇÃO DINÂMICA DA COR DE DESTAQUE DO WINDOWS 11
   ========================================================================== */
window.applyWindowsAccentColor = function (hexColor) {
  if (!hexColor || typeof hexColor !== "string" || !hexColor.startsWith("#")) return;
  document.documentElement.style.setProperty("--win-accent", hexColor);
  const syncOn = localStorage.getItem("sony_sync_win_accent") === "true";
  const sw = document.getElementById("swWinAccentSync");
  if (sw) sw.classList.toggle("on", syncOn);
  if (syncOn) {
    document.documentElement.style.setProperty("--ghub-cyan", hexColor);
  }
};

window.toggleWindowsAccentSync = function () {
  const current = localStorage.getItem("sony_sync_win_accent") === "true";
  const next = !current;
  localStorage.setItem("sony_sync_win_accent", next ? "true" : "false");
  const winAccent = getComputedStyle(document.documentElement).getPropertyValue("--win-accent").trim();
  const sw = document.getElementById("swWinAccentSync");
  if (sw) sw.classList.toggle("on", next);
  if (next && winAccent) {
    document.documentElement.style.setProperty("--ghub-cyan", winAccent);
    showToast(`Tema sincronizado com a cor do Windows 11 (${winAccent})!`, "🎨");
  } else {
    document.documentElement.style.setProperty("--ghub-cyan", "#00e5ff");
    showToast("Tema restaurado para Logitech G Cyan (#00e5ff)!", "🎨");
  }
};

/* ==========================================================================
   CONFIGURAÇÕES GERAIS, SISTEMA WINDOWS 11 & PREFERÊNCIAS
   ========================================================================== */
function toggleStartupClick() {
  const sw = document.getElementById("swStartup");
  if (!sw) return;
  const next = !sw.classList.contains("on");
  sw.classList.toggle("on", next);
  if (window.pywebview && window.pywebview.api && window.pywebview.api.set_run_at_startup) {
    window.pywebview.api.set_run_at_startup(next).then(() => {
      showToast(next ? "Inicialização com o Windows ativada!" : "Inicialização com o Windows desativada!", "🚀");
    });
  } else {
    showToast(next ? "Inicialização com o Windows ativada!" : "Inicialização com o Windows desativada!", "🚀");
  }
}
window.toggleStartupClick = toggleStartupClick;

function toggleCloseToTrayClick() {
  const sw = document.getElementById("swCloseToTray");
  if (!sw) return;
  const next = !sw.classList.contains("on");
  sw.classList.toggle("on", next);
  localStorage.setItem("sony_close_to_tray", next ? "true" : "false");
  if (window.pywebview && window.pywebview.api && window.pywebview.api.set_close_to_tray) {
    window.pywebview.api.set_close_to_tray(next);
  }
  showToast(next ? "Fechar janela minimiza para a bandeja!" : "Fechar janela encerra o aplicativo!", "📌");
}
window.toggleCloseToTrayClick = toggleCloseToTrayClick;

function toggleOverlayPrefClick() {
  const sw = document.getElementById("swOverlayPref");
  if (!sw) return;
  const next = !sw.classList.contains("on");
  sw.classList.toggle("on", next);
  localStorage.setItem("sony_show_overlay", next ? "true" : "false");
  showToast(next ? "Overlay estilo iOS ativado!" : "Overlay estilo iOS desativado!", "📱");
}
window.toggleOverlayPrefClick = toggleOverlayPrefClick;

function toggleLowBatToastClick() {
  const sw = document.getElementById("swLowBatToast");
  if (!sw) return;
  const next = !sw.classList.contains("on");
  sw.classList.toggle("on", next);
  localStorage.setItem("sony_low_bat_toast", next ? "true" : "false");
  showToast(next ? "Alerta de bateria baixa ativado!" : "Alerta de bateria baixa desativado!", "🪫");
}
window.toggleLowBatToastClick = toggleLowBatToastClick;

function toggleSplDosimeterClick() {
  const sw = document.getElementById("swSplDosimeter");
  if (!sw) return;
  const next = !sw.classList.contains("on");
  sw.classList.toggle("on", next);
  localStorage.setItem("sony_spl_dosimeter", next ? "true" : "false");
  if (!next) {
    stopHearingSafetyPoller();
  } else {
    startHearingSafetyPoller();
  }
  showToast(next ? "Dosímetro SPL ativo!" : "Dosímetro SPL pausado!", "🩺");
}
window.toggleSplDosimeterClick = toggleSplDosimeterClick;

initEqUI();
initAcousticLabUI();
renderAutomationRulesList();
