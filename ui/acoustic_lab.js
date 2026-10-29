/* ==========================================================================
   Sony Sound Connect PC — Laboratório Acústico ISO 226, Crossfeed 3D & Dosímetro SPL
   Created by Matheus Veras • Source-Available Proprietary (Ver LICENSE.md)
   ========================================================================== */

let webAudioCtx = null;
let audioIdleTimer = null;
let activeAudioEndTime = 0;

function getAudioContext() {
  if (!webAudioCtx) {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    webAudioCtx = new AudioContextClass({ latencyHint: "interactive" });
  }
  if (webAudioCtx.state === "suspended") {
    webAudioCtx.resume();
  }
  return webAudioCtx;
}

function scheduleAudioContextSuspend(durationSec) {
  if (!webAudioCtx) return;
  const targetEnd = webAudioCtx.currentTime + Math.max(0.1, durationSec);
  if (targetEnd > activeAudioEndTime) {
    activeAudioEndTime = targetEnd;
  }
  if (audioIdleTimer) clearTimeout(audioIdleTimer);
  audioIdleTimer = setTimeout(() => {
    if (!webAudioCtx || spatialDemoPlaying) return;
    if (webAudioCtx.currentTime >= activeAudioEndTime - 0.05 && webAudioCtx.state === "running") {
      webAudioCtx.suspend().catch(() => {});
    }
  }, Math.ceil(durationSec * 1000) + 320);
}

function suspendAudioContextNow() {
  if (audioIdleTimer) {
    clearTimeout(audioIdleTimer);
    audioIdleTimer = null;
  }
  if (webAudioCtx && webAudioCtx.state === "running") {
    webAudioCtx.suspend().catch(() => {});
  }
}

function playCommitChime() {
  if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  try {
    const ctx = getAudioContext();
    const now = ctx.currentTime;
    [880, 1318.5].forEach((freq, i) => {
      const osc = ctx.createOscillator();
      const g = ctx.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(freq, now + i * 0.055);
      g.gain.setValueAtTime(0.0001, now + i * 0.055);
      g.gain.exponentialRampToValueAtTime(0.032, now + i * 0.055 + 0.015);
      g.gain.exponentialRampToValueAtTime(0.0001, now + i * 0.055 + 0.16);
      osc.connect(g);
      g.connect(ctx.destination);
      osc.start(now + i * 0.055);
      osc.stop(now + i * 0.055 + 0.17);
    });
    scheduleAudioContextSuspend(0.28);
  } catch (_) {}
}

/* ==========================================================================
   TESTE AUDITIVO BIOMÉTRICO ISO 226:2023 / FLETCHER-MUNSON
   ========================================================================== */
const HEARING_FREQUENCIES = [
  { freq: 250, short: "250", tag: "Graves de Ressonância (ISO +11.2 dB)", isoOffsetDb: 11.2, alphaWeight: 0.58, defaultDb: -19 },
  { freq: 500, short: "500", tag: "Corpo & Médios-Graves (ISO +3.8 dB)", isoOffsetDb: 3.8, alphaWeight: 0.65, defaultDb: -26 },
  { freq: 1000, short: "1k", tag: "Âncora Vocal ISO 226 (0.0 dB Ref)", isoOffsetDb: 0.0, alphaWeight: 0.72, defaultDb: -30 },
  { freq: 2500, short: "2.5k", tag: "Canal Auditivo & Presença (ISO -3.2 dB)", isoOffsetDb: -3.2, alphaWeight: 0.68, defaultDb: -33 },
  { freq: 6300, short: "6.3k", tag: "Articulação & Harmônicos (ISO +4.6 dB)", isoOffsetDb: 4.6, alphaWeight: 0.62, defaultDb: -25 },
  { freq: 12000, short: "12k", tag: "Ar & Microdetalhes (ISO +11.8 dB)", isoOffsetDb: 11.8, alphaWeight: 0.54, defaultDb: -18 },
];

let currentHearingStep = 0;
let hearingCurrentDb = HEARING_FREQUENCIES[0].defaultDb;
let hearingUserSamples = [];
let currentBiometricCurve = [2, 0, 1, 3, 2, 2];
let biometricProfiles = [
  {
    id: "matheus-dia",
    name: "Matheus Dia (ISO 226 Reference)",
    clear_bass: 2,
    bands: [0, 1, 3, 2, 2],
    thresholds: [-17, -24, -28, -31, -23, -15],
  },
  {
    id: "matheus-noite",
    name: "Matheus Noite / Foco (Low-SPL)",
    clear_bass: 3,
    bands: [1, 0, 2, 2, 3],
    thresholds: [-15, -23, -28, -30, -22, -13],
  },
];
let selectedBioProfileId = "matheus-dia";

function computeIso226Compensation(thresholds) {
  if (!Array.isArray(thresholds) || thresholds.length < 6) {
    return [2, 0, 1, 3, 2, 2];
  }
  const anchor1k = thresholds[2];
  return HEARING_FREQUENCIES.map((spec, idx) => {
    const expectedIsoDb = anchor1k + spec.isoOffsetDb;
    const deficitDb = thresholds[idx] - expectedIsoDb;
    const compressedGain = Math.round(deficitDb * spec.alphaWeight);
    return Math.max(-8, Math.min(8, compressedGain));
  });
}

function renderBiometricProfileSelect() {
  const cmb = document.getElementById("cmbBioProfiles");
  if (!cmb) return;
  cmb.innerHTML = "";
  biometricProfiles.forEach((p) => {
    const opt = document.createElement("option");
    opt.value = p.id;
    opt.textContent = p.name;
    if (p.id === selectedBioProfileId) opt.selected = true;
    cmb.appendChild(opt);
  });
}

function renderBiometricComparisonGraph(curve6, labelTitle = "Curva Biométrica vs Referência Plana (0 dB)") {
  const curvePath = document.getElementById("bioCurvePath");
  const areaPath = document.getElementById("bioAreaPath");
  const nodesGroup = document.getElementById("bioNodesGroup");
  const titleEl = document.getElementById("lblBioCurveTitle");
  if (!curvePath || !areaPath || !nodesGroup) return;
  if (titleEl && labelTitle) titleEl.textContent = labelTitle;

  const w = 340;
  const midY = 38;
  const amp = 24;
  const xStart = 24;
  const xStep = (w - 48) / 5;

  const pts = curve6.map((db, i) => {
    const clamped = Math.max(-10, Math.min(10, db || 0));
    return {
      x: xStart + i * xStep,
      y: midY - (clamped / 10) * amp,
      db: clamped,
      lbl: HEARING_FREQUENCIES[i].short,
    };
  });

  let d = `M ${pts[0].x.toFixed(1)} ${pts[0].y.toFixed(1)}`;
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[i];
    const p1 = pts[i + 1];
    const mx = (p0.x + p1.x) / 2;
    d += ` C ${mx.toFixed(1)} ${p0.y.toFixed(1)}, ${mx.toFixed(1)} ${p1.y.toFixed(1)}, ${p1.x.toFixed(1)} ${p1.y.toFixed(1)}`;
  }

  curvePath.setAttribute("d", d);
  areaPath.setAttribute("d", `${d} L ${pts[5].x.toFixed(1)} ${midY} L ${pts[0].x.toFixed(1)} ${midY} Z`);

  let nodesHtml = "";
  pts.forEach((p, idx) => {
    const sign = p.db > 0 ? "+" : "";
    const color = idx === 0 ? "#e5c178" : "#00e5ff";
    nodesHtml += `
      <circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="3.4" fill="${color}" stroke="#07080b" stroke-width="1.4" />
      <text x="${p.x.toFixed(1)}" y="${(p.y <= midY ? Math.max(10, p.y - 6) : Math.min(72, p.y + 11)).toFixed(1)}" text-anchor="middle" fill="${color}" font-size="8.2" font-weight="700">${sign}${p.db}</text>
      <text x="${p.x.toFixed(1)}" y="74" text-anchor="middle" fill="#64748b" font-size="7.5" font-weight="600">${p.lbl}</text>
    `;
  });
  nodesGroup.innerHTML = nodesHtml;
}

function onSelectBioProfile(profileId) {
  const found = biometricProfiles.find((p) => p.id === profileId);
  if (!found) return;
  selectedBioProfileId = found.id;
  currentBiometricCurve = [found.clear_bass, ...(found.bands || [0, 0, 0, 0, 0])];
  const inp = document.getElementById("inpBioProfileName");
  if (inp) inp.value = found.name;
  renderBiometricComparisonGraph(currentBiometricCurve, `${found.name} vs 0 dB Flat`);
  const sum = document.getElementById("lblHearingSummary");
  if (sum) {
    const fmt = currentBiometricCurve.map((v) => (v >= 0 ? `+${v}` : `${v}`)).join(" / ");
    sum.textContent = `Compensação ISO 226: [${fmt}] dB`;
  }
}

function saveBiometricProfileUI() {
  const inp = document.getElementById("inpBioProfileName");
  const rawName = (inp && inp.value.trim()) ? inp.value.trim() : `Matheus Perfil ${biometricProfiles.length + 1}`;
  const cb = Math.round(currentBiometricCurve[0] || 0);
  const bands = currentBiometricCurve.slice(1).map((b) => Math.round(b || 0));
  const thresholds = hearingUserSamples.length === 6
    ? hearingUserSamples.map((s) => s.effectiveThresholdDb)
    : [-17, -24, -28, -31, -23, -15];

  if (window.pywebview && window.pywebview.api && window.pywebview.api.save_biometric_profile) {
    window.pywebview.api.save_biometric_profile(rawName, cb, bands, thresholds).then((updated) => {
      if (Array.isArray(updated) && updated.length) {
        biometricProfiles = updated;
        const last = updated.find((p) => p.name.toLowerCase() === rawName.toLowerCase()) || updated[updated.length - 1];
        selectedBioProfileId = last.id;
        renderBiometricProfileSelect();
        onSelectBioProfile(selectedBioProfileId);
      }
    });
  } else {
    const slug = rawName.toLowerCase().replace(/[^a-z0-9]+/g, "-") || `bio-${Date.now()}`;
    const entry = { id: slug, name: rawName, clear_bass: cb, bands, thresholds };
    const idx = biometricProfiles.findIndex((p) => p.id === slug);
    if (idx >= 0) biometricProfiles[idx] = entry;
    else biometricProfiles.push(entry);
    selectedBioProfileId = slug;
    try { localStorage.setItem("sony_bio_profiles", JSON.stringify(biometricProfiles)); } catch (_) {}
    renderBiometricProfileSelect();
    onSelectBioProfile(selectedBioProfileId);
  }
  playCommitChime();
  window.showToast && window.showToast(`Perfil auditivo "${rawName}" salvo!`, "💾");
}

function deleteCurrentBioProfile() {
  if (biometricProfiles.length <= 1) {
    window.showToast && window.showToast("Mantenha ao menos 1 perfil biométrico de referência.", "ℹ️");
    return;
  }
  const targetId = selectedBioProfileId;
  if (window.pywebview && window.pywebview.api && window.pywebview.api.delete_biometric_profile) {
    window.pywebview.api.delete_biometric_profile(targetId).then((updated) => {
      if (Array.isArray(updated) && updated.length) {
        biometricProfiles = updated;
        selectedBioProfileId = biometricProfiles[0].id;
        renderBiometricProfileSelect();
        onSelectBioProfile(selectedBioProfileId);
      }
    });
  } else {
    biometricProfiles = biometricProfiles.filter((p) => p.id !== targetId);
    selectedBioProfileId = biometricProfiles[0].id;
    try { localStorage.setItem("sony_bio_profiles", JSON.stringify(biometricProfiles)); } catch (_) {}
    renderBiometricProfileSelect();
    onSelectBioProfile(selectedBioProfileId);
  }
  window.showToast && window.showToast("Perfil biométrico removido.", "🗑️");
}

function playCurrentTestTone() {
  const ctx = getAudioContext();
  const idx = Math.min(currentHearingStep, HEARING_FREQUENCIES.length - 1);
  const freq = HEARING_FREQUENCIES[idx].freq;
  const gainVal = Math.pow(10, hearingCurrentDb / 20);

  const osc = ctx.createOscillator();
  const gain = ctx.createGain();

  osc.type = "sine";
  osc.frequency.setValueAtTime(freq, ctx.currentTime);

  gain.gain.setValueAtTime(0.0001, ctx.currentTime);
  gain.gain.exponentialRampToValueAtTime(Math.max(0.0001, gainVal), ctx.currentTime + 0.06);
  gain.gain.setValueAtTime(Math.max(0.0001, gainVal), ctx.currentTime + 0.72);
  gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.90);

  osc.connect(gain);
  gain.connect(ctx.destination);

  osc.start(ctx.currentTime);
  osc.stop(ctx.currentTime + 0.92);
  scheduleAudioContextSuspend(0.95);
}

function stepHearingVol(delta) {
  hearingCurrentDb = Math.max(-52, Math.min(-6, hearingCurrentDb + delta));
  const el = document.getElementById("lblToneDb");
  if (el) el.textContent = `${hearingCurrentDb} dB`;
  playCurrentTestTone();
}

function submitHearingSample(responseType) {
  if (currentHearingStep >= HEARING_FREQUENCIES.length) {
    resetHearingTest();
  }
  if (responseType === "inaudible") {
    hearingCurrentDb = Math.min(-6, hearingCurrentDb + 4);
    const el = document.getElementById("lblToneDb");
    if (el) el.textContent = `${hearingCurrentDb} dB`;
    playCurrentTestTone();
    return;
  }

  const effectiveThresholdDb = responseType === "clear" ? (hearingCurrentDb - 3) : hearingCurrentDb;
  hearingUserSamples.push({
    freq: HEARING_FREQUENCIES[currentHearingStep].freq,
    effectiveThresholdDb,
  });

  const partialThresholds = HEARING_FREQUENCIES.map((spec, i) =>
    hearingUserSamples[i] ? hearingUserSamples[i].effectiveThresholdDb : spec.defaultDb
  );
  currentBiometricCurve = computeIso226Compensation(partialThresholds);
  renderBiometricComparisonGraph(currentBiometricCurve, "Calibrando Curva ISO 226 em Tempo Real...");

  currentHearingStep++;
  if (currentHearingStep < HEARING_FREQUENCIES.length) {
    updateHearingStepUI();
    playCurrentTestTone();
  } else {
    finishHearingTest();
  }
}

function updateHearingStepUI() {
  const step = HEARING_FREQUENCIES[currentHearingStep];
  const stepEl = document.getElementById("lblHearingStep");
  const freqEl = document.getElementById("hearingFreqVal");
  const tagEl = document.getElementById("hearingFreqTag");
  const dbEl = document.getElementById("lblToneDb");
  if (stepEl) stepEl.textContent = `Etapa ${currentHearingStep + 1} / 6`;
  if (freqEl) {
    freqEl.textContent = step.freq.toLocaleString("pt-BR");
    freqEl.classList.remove("step-enter");
    void freqEl.offsetWidth;
    freqEl.classList.add("step-enter");
  }
  if (tagEl) tagEl.textContent = step.tag;
  hearingCurrentDb = step.defaultDb;
  if (dbEl) dbEl.textContent = `${hearingCurrentDb} dB`;
}

function resetHearingTest() {
  currentHearingStep = 0;
  hearingUserSamples = [];
  updateHearingStepUI();
  const sum = document.getElementById("lblHearingSummary");
  if (sum) sum.textContent = "Toque o tom puro de 250 Hz e indique seu limiar auditivo.";
  window.showToast && window.showToast("Teste biométrico ISO 226 reiniciado.", "🧬");
}

function finishHearingTest() {
  const finalThresholds = hearingUserSamples.map((s) => s.effectiveThresholdDb);
  currentBiometricCurve = computeIso226Compensation(finalThresholds);
  const stepEl = document.getElementById("lblHearingStep");
  if (stepEl) stepEl.textContent = "ISO 226 OK";
  renderBiometricComparisonGraph(currentBiometricCurve, "Curva Auditiva Calculada vs 0 dB Flat");
  const fmt = currentBiometricCurve.map((v) => (v >= 0 ? `+${v}` : `${v}`)).join(" / ");
  const sum = document.getElementById("lblHearingSummary");
  if (sum) sum.textContent = `Resultado ISO 226: [${fmt}] dB — Salve ou aplique no EQ!`;
  playCommitChime();
  window.showToast && window.showToast("🎉 Modelagem Auditiva ISO 226:2023 concluída!", "🧬");
}

function applyBiometricCurveToEq() {
  const activeProf = biometricProfiles.find((p) => p.id === selectedBioProfileId);
  const profLabel = (document.getElementById("inpBioProfileName")?.value || "").trim() || (activeProf ? activeProf.name : "Biométrico ISO 226");
  const compBands = currentBiometricCurve.slice(0, 6).map((b) => Math.max(-10, Math.min(10, Math.round(b))));

  eqTarget = compBands;
  startEqSpring();
  setActivePresetUI(`Bio: ${profLabel}`);
  if (window.pywebview && window.pywebview.api && window.pywebview.api.apply_autoeq_profile) {
    window.pywebview.api.apply_autoeq_profile(profLabel, compBands[0], compBands.slice(1));
  }
  playCommitChime();
  window.showToast && window.showToast(`Curva Biométrica "${profLabel}" aplicada ao DSP!`, "⚡");
}

/* ==========================================================================
   VIRTUALIZADOR 3D HRTF BIQUAD LINKWITZ / CHU-MOY + PONTE WINDOWS APO
   ========================================================================== */
const SPATIAL_PRESETS = {
  nearfield: { label: "Estúdio Near-Field", cutoffHz: 700, delaySec: 0.00028, baseCrossDb: -6.0, maxAngle: 60 },
  hifi:      { label: "Sala Acústica Hi-Fi", cutoffHz: 620, delaySec: 0.00034, baseCrossDb: -5.2, maxAngle: 72 },
  esports:   { label: "Gaming 3D FPS", cutoffHz: 880, delaySec: 0.00022, baseCrossDb: -6.8, maxAngle: 52 },
};

let spatialAudioEnabled = true;
let spatialCurrentMode = "nearfield";
let crossfeedWidth = 65;
let spatialAbBypass = false;
let spatialDemoPlaying = false;
let spatialDemoNodes = null;
let spatialDemoStopTimer = null;
let apoSpatialSyncDebounce = null;

function syncSpatialEngineToApo() {
  if (apoSpatialSyncDebounce) clearTimeout(apoSpatialSyncDebounce);
  apoSpatialSyncDebounce = setTimeout(() => {
    if (window.pywebview && window.pywebview.api && window.pywebview.api.sync_spatial_to_apo) {
      window.pywebview.api.sync_spatial_to_apo(spatialAudioEnabled && !spatialAbBypass, spatialCurrentMode, crossfeedWidth);
    }
  }, 160);
}

function computeLinkwitzMatrixParams() {
  const spec = SPATIAL_PRESETS[spatialCurrentMode] || SPATIAL_PRESETS.nearfield;
  const isActive = spatialAudioEnabled && !spatialAbBypass && crossfeedWidth > 0;
  const widthNorm = crossfeedWidth / 100;

  const refLinear = Math.pow(10, spec.baseCrossDb / 20);
  const crossLinear = isActive ? Math.min(0.58, refLinear * (widthNorm / 0.65)) : 0.0;
  const directLinear = 1.0 / Math.sqrt(1.0 + crossLinear * crossLinear);
  const shelfDb = isActive ? +(1.8 * Math.min(1.25, widthNorm / 0.65)).toFixed(2) : 0.0;
  const crossDbDisplay = crossLinear > 0.001 ? (20 * Math.log10(crossLinear)).toFixed(1) : "-∞";
  const angleDeg = Math.round(spec.maxAngle * widthNorm);

  return {
    cutoffHz: spec.cutoffHz,
    delaySec: spec.delaySec,
    crossLinear,
    directLinear,
    shelfDb,
    crossDbDisplay,
    angleDeg,
    isActive,
  };
}

function updateSpatialTelemetryUI() {
  const p = computeLinkwitzMatrixParams();
  const stageBox = document.getElementById("spatialStageBox");
  if (stageBox) stageBox.classList.toggle("spatial-off", !p.isActive);

  const podL = document.getElementById("podL");
  const podR = document.getElementById("podR");
  const podC = document.getElementById("podCenter");
  if (podL) podL.textContent = `L (${p.isActive ? p.angleDeg : 90}°)`;
  if (podR) podR.textContent = `R (${p.isActive ? p.angleDeg : 90}°)`;
  if (podC) podC.textContent = p.isActive ? "Phantom Center 3D" : "Bypass Estéreo Seco";

  const specsEl = document.getElementById("lblHrtfSpecs");
  if (specsEl) {
    const us = Math.round(p.delaySec * 1e6);
    specsEl.innerHTML = `
      <span>LPF: <strong style="color: var(--ghub-cyan);">${p.cutoffHz} Hz</strong></span>
      <span>Cross: <strong style="color: var(--sony-copper-bright);">${p.crossDbDisplay} dB</strong></span>
      <span>ITD: <strong style="color: var(--emerald);">${p.isActive ? us : 0} µs</strong></span>
    `;
  }

  const abBtn = document.getElementById("btnSpatialAB");
  if (abBtn) {
    abBtn.innerHTML = p.isActive ? "<span>🔀 A/B: 3D HRTF ON</span>" : "<span>🔀 A/B: Estéreo Seco</span>";
    abBtn.style.borderColor = p.isActive ? "rgba(0, 229, 255, 0.45)" : "var(--border-hairline)";
  }

  if (spatialDemoNodes && webAudioCtx) {
    const now = webAudioCtx.currentTime;
    const tau = 0.018;
    spatialDemoNodes.lpfLR.frequency.setTargetAtTime(p.cutoffHz, now, tau);
    spatialDemoNodes.lpfRL.frequency.setTargetAtTime(p.cutoffHz, now, tau);
    spatialDemoNodes.delayLR.delayTime.setTargetAtTime(p.delaySec, now, tau);
    spatialDemoNodes.delayRL.delayTime.setTargetAtTime(p.delaySec, now, tau);
    spatialDemoNodes.crossGainLR.gain.setTargetAtTime(p.crossLinear, now, tau);
    spatialDemoNodes.crossGainRL.gain.setTargetAtTime(p.crossLinear, now, tau);
    spatialDemoNodes.directGainL.gain.setTargetAtTime(p.directLinear, now, tau);
    spatialDemoNodes.directGainR.gain.setTargetAtTime(p.directLinear, now, tau);
    spatialDemoNodes.shelfL.gain.setTargetAtTime(p.shelfDb, now, tau);
    spatialDemoNodes.shelfR.gain.setTargetAtTime(p.shelfDb, now, tau);
  }
}

window.applyAutomationSpatialUI = function (cfg) {
  if (!cfg) return;
  spatialAudioEnabled = !!cfg.enabled;
  spatialAbBypass = false;
  if (cfg.mode && SPATIAL_PRESETS[cfg.mode]) {
    spatialCurrentMode = cfg.mode;
  }
  document.getElementById("swSpatialAudio")?.classList.toggle("on", spatialAudioEnabled);
  ["nearfield", "hifi", "esports"].forEach((m) => {
    document.getElementById(`spMode-${m}`)?.classList.toggle("active", m === spatialCurrentMode);
  });
  updateSpatialTelemetryUI();
};

function toggleSpatialAudioEngine() {
  const sw = document.getElementById("swSpatialAudio");
  spatialAudioEnabled = sw.classList.toggle("on");
  if (spatialAudioEnabled) spatialAbBypass = false;
  updateSpatialTelemetryUI();
  syncSpatialEngineToApo();
  window.showToast && window.showToast(`Áudio Espacial 3D ${spatialAudioEnabled ? "ativado" : "desativado"}`, "🌌");
}

function selectSpatialMode(mode) {
  spatialCurrentMode = mode;
  ["nearfield", "hifi", "esports"].forEach((m) => {
    const card = document.getElementById(`spMode-${m}`);
    if (card) card.classList.toggle("active", m === mode);
  });
  updateSpatialTelemetryUI();
  syncSpatialEngineToApo();
  const spec = SPATIAL_PRESETS[mode] || SPATIAL_PRESETS.nearfield;
  window.showToast && window.showToast(`Topologia Biquad: ${spec.label} (${spec.cutoffHz}Hz / ${Math.round(spec.delaySec * 1e6)}µs)`, "🎧");
}

function onCrossfeedSlider(val) {
  crossfeedWidth = parseInt(val, 10);
  const el = document.getElementById("lblCrossfeedVal");
  if (el) el.textContent = `${crossfeedWidth}%`;
  updateSpatialTelemetryUI();
  syncSpatialEngineToApo();
}

function toggleSpatialABComparison() {
  if (!spatialAudioEnabled) {
    spatialAudioEnabled = true;
    document.getElementById("swSpatialAudio")?.classList.add("on");
    spatialAbBypass = false;
  } else {
    spatialAbBypass = !spatialAbBypass;
  }
  updateSpatialTelemetryUI();
  syncSpatialEngineToApo();
  window.showToast && window.showToast(
    spatialAbBypass
      ? "Modo B: Estéreo Seco Isolado (Sem Crossfeed)"
      : "Modo A: Crossfeed 3D Linkwitz Biquad Ativo!",
    "🔀"
  );
}

function stopSpatialDemoPlayback(silent = false) {
  if (spatialDemoStopTimer) {
    clearTimeout(spatialDemoStopTimer);
    spatialDemoStopTimer = null;
  }
  if (spatialDemoNodes) {
    try {
      spatialDemoNodes.sources.forEach((s) => {
        try { s.stop(); } catch (_) {}
      });
      spatialDemoNodes.masterOut.disconnect();
    } catch (_) {}
    spatialDemoNodes = null;
  }
  spatialDemoPlaying = false;
  const btn = document.getElementById("btnSpatialDemo");
  if (btn) btn.innerHTML = "<span>✨ Ouvir Demo 3D Linkwitz</span>";
  if (!silent) {
    scheduleAudioContextSuspend(0.15);
  }
}

function playSpatialDemoAudio() {
  if (spatialDemoPlaying) {
    stopSpatialDemoPlayback(false);
    return;
  }

  const ctx = getAudioContext();
  const now = ctx.currentTime;
  const p = computeLinkwitzMatrixParams();

  const inputBus = ctx.createGain();
  const splitter = ctx.createChannelSplitter(2);
  const merger = ctx.createChannelMerger(2);
  const masterOut = ctx.createGain();
  masterOut.gain.setValueAtTime(0.85, now);

  const shelfL = ctx.createBiquadFilter();
  shelfL.type = "highshelf";
  shelfL.frequency.setValueAtTime(720, now);
  shelfL.gain.setValueAtTime(p.shelfDb, now);

  const shelfR = ctx.createBiquadFilter();
  shelfR.type = "highshelf";
  shelfR.frequency.setValueAtTime(720, now);
  shelfR.gain.setValueAtTime(p.shelfDb, now);

  const directGainL = ctx.createGain();
  directGainL.gain.setValueAtTime(p.directLinear, now);
  const directGainR = ctx.createGain();
  directGainR.gain.setValueAtTime(p.directLinear, now);

  const lpfLR = ctx.createBiquadFilter();
  lpfLR.type = "lowpass";
  lpfLR.frequency.setValueAtTime(p.cutoffHz, now);
  lpfLR.Q.setValueAtTime(0.7071, now);

  const lpfRL = ctx.createBiquadFilter();
  lpfRL.type = "lowpass";
  lpfRL.frequency.setValueAtTime(p.cutoffHz, now);
  lpfRL.Q.setValueAtTime(0.7071, now);

  const delayLR = ctx.createDelay(0.01);
  delayLR.delayTime.setValueAtTime(p.delaySec, now);
  const delayRL = ctx.createDelay(0.01);
  delayRL.delayTime.setValueAtTime(p.delaySec, now);

  const crossGainLR = ctx.createGain();
  crossGainLR.gain.setValueAtTime(p.crossLinear, now);
  const crossGainRL = ctx.createGain();
  crossGainRL.gain.setValueAtTime(p.crossLinear, now);

  inputBus.connect(splitter);
  splitter.connect(shelfL, 0);
  shelfL.connect(directGainL);
  directGainL.connect(merger, 0, 0);

  splitter.connect(shelfR, 1);
  shelfR.connect(directGainR);
  directGainR.connect(merger, 0, 1);

  splitter.connect(lpfLR, 0);
  lpfLR.connect(delayLR);
  delayLR.connect(crossGainLR);
  crossGainLR.connect(merger, 0, 1);

  splitter.connect(lpfRL, 1);
  lpfRL.connect(delayRL);
  delayRL.connect(crossGainRL);
  crossGainRL.connect(merger, 0, 0);

  merger.connect(masterOut);
  masterOut.connect(ctx.destination);

  const notes = [
    { t: 0.00, dur: 0.65, freq: 261.63, pan: -0.94, type: "triangle" },
    { t: 0.48, dur: 0.65, freq: 329.63, pan:  0.94, type: "triangle" },
    { t: 0.96, dur: 0.70, freq: 392.00, pan: -0.92, type: "triangle" },
    { t: 1.44, dur: 0.75, freq: 493.88, pan:  0.92, type: "sine"     },
    { t: 1.96, dur: 0.85, freq: 523.25, pan: -0.88, type: "triangle" },
    { t: 2.48, dur: 0.85, freq: 659.25, pan:  0.88, type: "sine"     },
    { t: 3.00, dur: 1.15, freq: 196.00, pan:  0.00, type: "sine"     },
    { t: 3.00, dur: 1.15, freq: 587.33, pan: -0.90, type: "triangle" },
    { t: 3.00, dur: 1.15, freq: 783.99, pan:  0.90, type: "sine"     },
  ];

  const sources = [];
  notes.forEach((n) => {
    const osc = ctx.createOscillator();
    const toneFilter = ctx.createBiquadFilter();
    const env = ctx.createGain();
    const panner = ctx.createStereoPanner();

    osc.type = n.type;
    osc.frequency.setValueAtTime(n.freq, now + n.t);
    toneFilter.type = "lowpass";
    toneFilter.frequency.setValueAtTime(n.freq * 4.5, now + n.t);
    panner.pan.setValueAtTime(n.pan, now + n.t);

    env.gain.setValueAtTime(0.0001, now + n.t);
    env.gain.exponentialRampToValueAtTime(0.16, now + n.t + 0.035);
    env.gain.exponentialRampToValueAtTime(0.0001, now + n.t + n.dur);

    osc.connect(toneFilter);
    toneFilter.connect(env);
    env.connect(panner);
    panner.connect(inputBus);

    osc.start(now + n.t);
    osc.stop(now + n.t + n.dur + 0.04);
    sources.push(osc);
  });

  const totalDur = 4.25;
  spatialDemoPlaying = true;
  spatialDemoNodes = {
    sources,
    masterOut,
    shelfL,
    shelfR,
    directGainL,
    directGainR,
    lpfLR,
    lpfRL,
    delayLR,
    delayRL,
    crossGainLR,
    crossGainRL,
  };

  const btn = document.getElementById("btnSpatialDemo");
  if (btn) btn.innerHTML = "<span>⏹️ Parar Demo (Teste o botão A/B!)</span>";

  spatialDemoStopTimer = setTimeout(() => {
    stopSpatialDemoPlayback(false);
  }, Math.ceil(totalDur * 1000));
  scheduleAudioContextSuspend(totalDur + 0.15);

  window.showToast && window.showToast("Demo 3D ativa: clique em '🔀 A/B' ou mova o slider ao vivo!", "✨");
}

/* ==========================================================================
   DOSÍMETRO DE SAÚDE AUDITIVA dB SPL (APPLE IOS HEADPHONE SAFETY • COREAUDIO)
   ========================================================================== */
let hearingSafetyInterval = null;

function renderHearingSafetyUI(data) {
  if (!data) return;
  const chip = document.getElementById("safetyChip");
  const chipText = document.getElementById("lblSafetyChip");
  const splEl = document.getElementById("lblSafetySpl");
  const zoneEl = document.getElementById("lblSafetyZone");
  const doseEl = document.getElementById("lblSafetyDose");
  const fillEl = document.getElementById("safetyMeterFill");

  const spl = typeof data.spl_db === "number" ? data.spl_db : 34.0;
  const zone = data.zone || "silent";

  if (chip && chipText) {
    chip.classList.remove("safe", "moderate", "loud", "silent");
    chip.classList.add(zone);
    if (zone === "silent") {
      chipText.textContent = "Silêncio • OMS OK";
    } else if (zone === "loud") {
      chipText.textContent = `⚠️ ${spl.toFixed(0)} dB • Alto`;
    } else {
      chipText.textContent = `${spl.toFixed(0)} dB • ${zone === "moderate" ? "Moderado" : "Seguro"}`;
    }
  }

  if (splEl) splEl.textContent = `${spl.toFixed(1)} dB SPL`;
  if (zoneEl) zoneEl.textContent = `${data.status_label || "Seguro"} • Vol Win ${data.windows_vol_pct || 0}%`;
  if (doseEl) doseEl.textContent = `Dose OMS: ${(data.daily_dose_pct || 0).toFixed(1)}%`;
  if (fillEl) {
    const ratio = Math.max(0.06, Math.min(1.0, (spl - 30) / 75));
    fillEl.style.transform = `scaleX(${ratio.toFixed(3)})`;
  }
}

function pollHearingSafetyOnce() {
  if (document.hidden || window.__hostWindowHidden) return;
  if (window.pywebview && window.pywebview.api && window.pywebview.api.get_hearing_safety_telemetry) {
    window.pywebview.api.get_hearing_safety_telemetry().then(renderHearingSafetyUI).catch(() => {});
  }
}

function startHearingSafetyPoller() {
  if (hearingSafetyInterval) return;
  pollHearingSafetyOnce();
  hearingSafetyInterval = setInterval(pollHearingSafetyOnce, 2500);
}

function stopHearingSafetyPoller() {
  if (hearingSafetyInterval) {
    clearInterval(hearingSafetyInterval);
    hearingSafetyInterval = null;
  }
}

function initAcousticLabUI() {
  try {
    const cached = localStorage.getItem("sony_bio_profiles");
    if (cached) {
      const parsed = JSON.parse(cached);
      if (Array.isArray(parsed) && parsed.length) biometricProfiles = parsed;
    }
  } catch (_) {}
  renderBiometricProfileSelect();
  onSelectBioProfile(selectedBioProfileId);
  updateHearingStepUI();
  updateSpatialTelemetryUI();
  startHearingSafetyPoller();
}
