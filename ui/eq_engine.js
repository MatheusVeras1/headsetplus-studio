/* ==========================================================================
   HeadsetPlus Studio — Motor Gráfico de Equalização & Banco AutoEq™
   Created by Matheus Veras • Source-Available Proprietary (Ver LICENSE.md)
   ========================================================================== */

const BAND_LABELS = ["Clear Bass", "400 Hz", "1 kHz", "2.5 kHz", "6.3 kHz", "16 kHz"];
const HARDWARE_PRESET_NAMES = [
  "Manual (Custom)",
  "Desligado (Off)",
  "Empolgado (Excited)",
  "Brilhante (Bright)",
  "Suave (Mellow)",
  "Relaxado (Relaxed)",
  "Vocal",
  "Agudos (Treble)",
  "Graves (Bass)",
  "Fala (Speech)",
  "Personalizado 1",
  "Personalizado 2",
];

let eqTarget = [3, -1, 2, 4, 4, 2];
let eqCurrent = [3, -1, 2, 4, 4, 2];
let eqVelocity = [0, 0, 0, 0, 0, 0];
let eqSpringRunning = false;
let draggingIdx = -1;
let hoveredBandIdx = -1;
let activePresetName = "Audiófilo (Comunidade)";

try {
  const cachedEq = localStorage.getItem("sony_saved_eq");
  if (cachedEq) {
    const p = JSON.parse(cachedEq);
    if (typeof p.clearBass === "number" && Array.isArray(p.bands) && p.bands.length >= 5) {
      eqTarget = [p.clearBass, ...p.bands.slice(0, 5)];
      eqCurrent = [p.clearBass, ...p.bands.slice(0, 5)];
      if (p.presetName) activePresetName = p.presetName;
    }
  }
} catch (_) {}

// Dimensões dinâmicas 1:1 em pixels reais do gráfico SVG (nunca distorce!)
let svgW = 660;
let svgH = 190;

function rubberband(overshoot, dimension, constant = 0.55) {
  return (overshoot * dimension * constant) / (dimension + constant * Math.abs(overshoot));
}

function getBandX(idx) {
  const colW = svgW / 6;
  return colW * (idx + 0.5);
}

function dbToY(db) {
  const midY = svgH / 2;
  const maxAmp = Math.max(40, (svgH / 2) - 28);
  return midY - (db / 10) * maxAmp;
}

function yToDb(y) {
  const midY = svgH / 2;
  const maxAmp = Math.max(40, (svgH / 2) - 28);
  return ((midY - y) / maxAmp) * 10;
}

function initPresetPopover() {
  const menu = document.getElementById("presetPopoverMenu");
  if (!menu) return;
  menu.innerHTML = "";
  HARDWARE_PRESET_NAMES.forEach((name) => {
    const item = document.createElement("div");
    item.className = "popover-item" + (name === activePresetName ? " selected" : "");
    item.textContent = name;
    item.onclick = () => {
      setActivePresetUI(name);
      menu.classList.remove("open");
      onHardwarePresetChange(name);
    };
    menu.appendChild(item);
  });
}

function setActivePresetUI(name) {
  activePresetName = name;
  const lbl = document.getElementById("lblActivePreset");
  if (lbl) lbl.textContent = name;
  document.querySelectorAll("#presetPopoverMenu .popover-item").forEach((el) => {
    el.classList.toggle("selected", el.textContent === name);
  });
  const nLow = (name || "").toLowerCase();
  document.querySelectorAll("#presetLibraryList .preset-card").forEach((card) => {
    const cardPreset = (card.getAttribute("data-preset") || "").toLowerCase();
    const isMatch = (cardPreset && (nLow.includes(cardPreset) || cardPreset.includes(nLow)))
      || (nLow.includes("audiófilo") && cardPreset.includes("audiófilo"))
      || (nLow.includes("empolgado") && cardPreset.includes("empolgado"))
      || (nLow.includes("gaming") && cardPreset.includes("gaming"))
      || (nLow.includes("voz") && cardPreset.includes("voz"))
      || (nLow.includes("cinema") && cardPreset.includes("cinema"));
    card.classList.toggle("active", !!isMatch);
  });
}
window.setActivePresetUI = setActivePresetUI;

function togglePresetPopover(e) {
  e.stopPropagation();
  document.getElementById("presetPopoverMenu")?.classList.toggle("open");
}

window.addEventListener("pointerdown", (e) => {
  const wrap = document.getElementById("presetPopoverWrap");
  if (wrap && !wrap.contains(e.target)) {
    document.getElementById("presetPopoverMenu")?.classList.remove("open");
  }
});

function initEqUI() {
  initPresetPopover();

  const row = document.getElementById("eqBandsRow");
  if (!row) return;
  row.innerHTML = "";
  BAND_LABELS.forEach((name, idx) => {
    const pill = document.createElement("div");
    pill.className = "band-pill" + (idx === 0 ? " clear-bass" : "");
    pill.innerHTML = `
      <span class="micro-label" style="${idx === 0 ? 'color: var(--sony-copper-bright);' : ''}">${name}</span>
      <span class="band-val tabular" id="bandVal-${idx}">0</span>
      <div class="band-step-btns">
        <button class="step-btn" onclick="stepBand(${idx}, -1)" aria-label="Diminuir ${name}">−</button>
        <button class="step-btn" onclick="stepBand(${idx}, 1)" aria-label="Aumentar ${name}">+</button>
      </div>
    `;
    pill.addEventListener("pointerenter", () => {
      hoveredBandIdx = idx;
      renderEqGraph();
    });
    pill.addEventListener("pointerleave", () => {
      hoveredBandIdx = -1;
      renderEqGraph();
    });
    pill.addEventListener("wheel", (e) => {
      e.preventDefault();
      stepBand(idx, e.deltaY < 0 ? 1 : -1);
    });
    row.appendChild(pill);
  });

  const nodesGroup = document.getElementById("eqNodesGroup");
  if (!nodesGroup) return;
  nodesGroup.innerHTML = "";
  BAND_LABELS.forEach((_, idx) => {
    const g = document.createElementNS("http://www.w3.org/2000/svg", "g");

    const guide = document.createElementNS("http://www.w3.org/2000/svg", "line");
    guide.setAttribute("id", `nodeGuide-${idx}`);
    guide.setAttribute("class", "eq-guide-line");

    const halo = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    halo.setAttribute("id", `nodeHalo-${idx}`);
    halo.setAttribute("r", 13);
    halo.setAttribute("fill", idx === 0 ? "rgba(229, 193, 120, 0.2)" : "rgba(0, 229, 255, 0.2)");

    const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    circle.setAttribute("id", `nodeDot-${idx}`);
    circle.setAttribute("class", "eq-node");
    circle.setAttribute("r", 6.5);
    circle.setAttribute("fill", idx === 0 ? "#e5c178" : "#00e5ff");
    circle.setAttribute("stroke", "#080a0f");
    circle.setAttribute("stroke-width", "2.2");

    const badge = document.createElementNS("http://www.w3.org/2000/svg", "text");
    badge.setAttribute("id", `nodeBadge-${idx}`);
    badge.setAttribute("text-anchor", "middle");
    badge.setAttribute("font-size", "10.5");
    badge.setAttribute("font-weight", "700");
    badge.setAttribute("fill", idx === 0 ? "#e5c178" : "#cbd5e1");
    badge.style.pointerEvents = "none";

    circle.addEventListener("pointerdown", (e) => {
      e.preventDefault();
      e.stopPropagation();
      circle.setPointerCapture(e.pointerId);
      draggingIdx = idx;
      circle.setAttribute("r", 8.5);
      halo.setAttribute("r", 17);
    });

    circle.addEventListener("pointermove", (e) => {
      if (draggingIdx !== idx) return;
      const svg = document.getElementById("eqSvg");
      const rect = svg.getBoundingClientRect();
      const relY = e.clientY - rect.top;
      let rawDb = yToDb(relY);
      if (rawDb > 10) {
        rawDb = 10 + rubberband(rawDb - 10, 4);
      } else if (rawDb < -10) {
        rawDb = -10 - rubberband(-10 - rawDb, 4);
      }
      eqCurrent[idx] = rawDb;
      eqTarget[idx] = Math.max(-10, Math.min(10, Math.round(rawDb)));
      eqVelocity[idx] = 0;
      renderEqGraph();
    });

    const endDrag = () => {
      if (draggingIdx !== idx) return;
      draggingIdx = -1;
      circle.setAttribute("r", 6.5);
      halo.setAttribute("r", 13);
      startEqSpring();
      commitEqToHardware();
    };

    circle.addEventListener("pointerup", endDrag);
    circle.addEventListener("pointercancel", endDrag);

    g.appendChild(guide);
    g.appendChild(halo);
    g.appendChild(circle);
    g.appendChild(badge);
    nodesGroup.appendChild(g);
  });

  const box = document.getElementById("eqGraphBox");
  if (box && typeof ResizeObserver !== "undefined") {
    const ro = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const w = Math.max(300, Math.round(entry.contentRect.width));
        const h = Math.max(140, Math.round(entry.contentRect.height));
        svgW = w;
        svgH = h;
        const svg = document.getElementById("eqSvg");
        if (svg) svg.setAttribute("viewBox", `0 0 ${svgW} ${svgH}`);
        renderGridLines();
        renderEqGraph();
      }
    });
    ro.observe(box);
  }

  applySavedEqToUI(activePresetName, eqTarget[0], eqTarget.slice(1));
}

function renderGridLines() {
  const g = document.getElementById("eqGridGroup");
  if (!g) return;
  const yTop = dbToY(10).toFixed(1);
  const yMid = dbToY(0).toFixed(1);
  const yBot = dbToY(-10).toFixed(1);
  g.innerHTML = `
    <line x1="0" y1="${yTop}" x2="${svgW}" y2="${yTop}" stroke="rgba(255,255,255,0.05)" stroke-dasharray="3,4" />
    <line x1="0" y1="${yMid}" x2="${svgW}" y2="${yMid}" stroke="rgba(255,255,255,0.13)" stroke-dasharray="5,5" />
    <line x1="0" y1="${yBot}" x2="${svgW}" y2="${yBot}" stroke="rgba(255,255,255,0.05)" stroke-dasharray="3,4" />
    <text x="12" y="${parseFloat(yTop) - 5}" fill="#64748b" font-size="10" font-weight="600">+10 dB</text>
    <text x="12" y="${parseFloat(yMid) - 6}" fill="#94a3b8" font-size="10" font-weight="600">0 dB</text>
    <text x="12" y="${parseFloat(yBot) - 6}" fill="#64748b" font-size="10" font-weight="600">-10 dB</text>
  `;
}

function renderEqGraph() {
  const curveEl = document.getElementById("eqCurvePath");
  const areaEl = document.getElementById("eqAreaPath");
  if (!curveEl || !areaEl) return;

  const pts = BAND_LABELS.map((_, i) => ({ x: getBandX(i), y: dbToY(eqCurrent[i]) }));

  pts.forEach((p, i) => {
    const guide = document.getElementById(`nodeGuide-${i}`);
    const dot = document.getElementById(`nodeDot-${i}`);
    const halo = document.getElementById(`nodeHalo-${i}`);
    const badge = document.getElementById(`nodeBadge-${i}`);

    if (guide) {
      guide.setAttribute("x1", p.x.toFixed(1));
      guide.setAttribute("x2", p.x.toFixed(1));
      guide.setAttribute("y1", 16);
      guide.setAttribute("y2", svgH);
      guide.classList.toggle("highlighted", i === hoveredBandIdx || i === draggingIdx);
    }

    if (dot && halo) {
      dot.setAttribute("cx", p.x.toFixed(1));
      dot.setAttribute("cy", p.y.toFixed(1));
      halo.setAttribute("cx", p.x.toFixed(1));
      halo.setAttribute("cy", p.y.toFixed(1));
    }

    const rounded = Math.round(eqCurrent[i]);
    const txt = (rounded > 0 ? "+" : "") + rounded;

    if (badge) {
      badge.setAttribute("x", p.x.toFixed(1));
      badge.setAttribute("y", (p.y - 14).toFixed(1));
      badge.textContent = `${txt} dB`;
    }

    const valEl = document.getElementById(`bandVal-${i}`);
    if (valEl) valEl.textContent = txt;
  });

  let d = `M 0 ${pts[0].y.toFixed(1)} L ${pts[0].x.toFixed(1)} ${pts[0].y.toFixed(1)}`;
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[i];
    const p1 = pts[i + 1];
    const midX = (p0.x + p1.x) / 2;
    d += ` C ${midX.toFixed(1)} ${p0.y.toFixed(1)}, ${midX.toFixed(1)} ${p1.y.toFixed(1)}, ${p1.x.toFixed(1)} ${p1.y.toFixed(1)}`;
  }
  d += ` L ${svgW} ${pts[pts.length - 1].y.toFixed(1)}`;

  curveEl.setAttribute("d", d);
  areaEl.setAttribute("d", `${d} L ${svgW} ${svgH} L 0 ${svgH} Z`);
}

function startEqSpring() {
  if (document.hidden || window.__hostWindowHidden) {
    for (let i = 0; i < 6; i++) {
      eqCurrent[i] = eqTarget[i];
      eqVelocity[i] = 0;
    }
    eqSpringRunning = false;
    renderEqGraph();
    return;
  }
  if (eqSpringRunning) return;
  eqSpringRunning = true;
  let lastTime = performance.now();

  function step(now) {
    const dt = Math.min(0.032, (now - lastTime) / 1000);
    lastTime = now;
    let stillMoving = false;

    const stiffness = 260;
    const damping = 32;

    for (let i = 0; i < 6; i++) {
      if (i === draggingIdx) continue;
      const disp = eqCurrent[i] - eqTarget[i];
      const force = -stiffness * disp - damping * eqVelocity[i];
      eqVelocity[i] += force * dt;
      eqCurrent[i] += eqVelocity[i] * dt;

      if (Math.abs(disp) > 0.02 || Math.abs(eqVelocity[i]) > 0.05) {
        stillMoving = true;
      } else {
        eqCurrent[i] = eqTarget[i];
        eqVelocity[i] = 0;
      }
    }

    renderEqGraph();
    if (stillMoving) {
      requestAnimationFrame(step);
    } else {
      eqSpringRunning = false;
    }
  }

  requestAnimationFrame(step);
}

function stepBand(idx, delta) {
  eqTarget[idx] = Math.max(-10, Math.min(10, eqTarget[idx] + delta));
  setActivePresetUI("Manual (Custom)");
  startEqSpring();
  commitEqToHardware();
}

function resetEqFlat() {
  eqTarget = [0, 0, 0, 0, 0, 0];
  setActivePresetUI("Desligado (Off)");
  startEqSpring();
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.set_eq_custom("Desligado (Off)", 0, [0, 0, 0, 0, 0]);
  }
  window.showToast && window.showToast("Equalizador resetado para 0 dB (Flat)", "⭕");
}

function applyQuickProfile(profileName, clearBass, bands) {
  const cleanBands = Array.isArray(bands) ? bands.slice(0, 5) : [0, 0, 0, 0, 0];
  const cb = Number(clearBass) || 0;
  eqTarget = [cb, ...cleanBands];
  setActivePresetUI(profileName);
  startEqSpring();
  try {
    localStorage.setItem(
      "sony_saved_eq",
      JSON.stringify({ presetName: profileName, clearBass: cb, bands: cleanBands })
    );
  } catch (_) {}
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.set_eq_custom(profileName, cb, cleanBands);
  }
  window.showToast && window.showToast(`Perfil aplicado: ${profileName}`, "🎚️");
}

function applySavedEqToUI(presetName, clearBass, bands) {
  const cb = typeof clearBass === "number" ? clearBass : 3;
  const bds = Array.isArray(bands) ? bands.slice(0, 5) : [-1, 2, 4, 4, 2];
  const pName = presetName || "Audiófilo (Comunidade)";
  eqTarget = [cb, ...bds];
  eqCurrent = [cb, ...bds];
  setActivePresetUI(pName);
  renderEqGraph();
  try {
    localStorage.setItem(
      "sony_saved_eq",
      JSON.stringify({ presetName: pName, clearBass: cb, bands: bds })
    );
  } catch (_) {}
}
window.applySavedEqToUI = applySavedEqToUI;

function commitEqToHardware() {
  const cb = Math.round(eqTarget[0]);
  const bands = eqTarget.slice(1).map((x) => Math.round(x));
  setActivePresetUI("Manual (Custom)");
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.set_eq_custom("Manual (Custom)", cb, bands);
  }
}

function onHardwarePresetChange(presetName) {
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.set_eq_preset_only(presetName);
  }
  window.showToast && window.showToast(`Preset nativo: ${presetName}`, "🎵");
}

function saveCurrentAsCustomProfile() {
  const cb = Math.round(eqTarget[0]);
  const bands = eqTarget.slice(1).map((x) => Math.round(x));
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.save_user_preset(cb, bands);
  }
  window.showToast && window.showToast(`Perfil salvo (${cb >= 0 ? "+" + cb : cb} dB Clear Bass)`, "💾");
}

/* ==========================================================================
   MOTOR DE CALIBRAÇÃO AUDIÓFILA AUTOEQ (+5.000 FONES COMPENSADOS)
   ========================================================================== */
let currentAutoEqBrand = "all";
let autoEqSearchQuery = "";
let autoEqCache = [];

const LOCAL_AUTOEQ_FALLBACK = [
  {
    name: "Sony WF-1000XM3 (Harman Neutral)",
    brand: "Sony",
    clear_bass: 2,
    bands: [-1, 2, 4, 3, 2],
    desc: "Referência Harman: corrige o recuo dos médios-altos (2.5kHz) e dá clareza vocal cristalina.",
  },
  {
    name: "Sony WH-1000XM4 (Over-Ear Harman)",
    brand: "Sony",
    clear_bass: -2,
    bands: [-2, 1, 3, 4, 1],
    desc: "Reduz o excesso de graves de fábrica e abre o palco sonoro e os harmônicos de cordas.",
  },
  {
    name: "Apple AirPods Pro 2 (USB-C / Lightning)",
    brand: "Apple",
    clear_bass: 1,
    bands: [0, 0, 1, 2, 2],
    desc: "Realce fino nos agudos superiores mantendo a excelente assinatura quase Harman original.",
  },
  {
    name: "Samsung Galaxy Buds 2 Pro",
    brand: "Samsung",
    clear_bass: 0,
    bands: [0, 0, 0, 1, 1],
    desc: "Linearização de resposta acústica de estúdio baseada na curva Harman In-Ear 2019.",
  },
  {
    name: "realme Buds Air 5 Pro (Dual Driver Coaxial)",
    brand: "Realme",
    clear_bass: 1,
    bands: [-2, 0, 3, 2, 1],
    desc: "Domina o subgrave agressivo de fábrica e extrai a máxima resolução do planar tweeter integrado.",
  },
  {
    name: "Sennheiser Momentum 4 Wireless",
    brand: "Sennheiser",
    clear_bass: -3,
    bands: [-2, 1, 2, 3, 2],
    desc: "Abaixa a ênfase excessiva em 100Hz para uma resposta equilibrada com fidelidade de estúdio.",
  },
];

function switchPresetSubTab(tab) {
  const btnPresets = document.getElementById("segBtnPresets");
  const btnAutoEq = document.getElementById("segBtnAutoEq");
  const listPresets = document.getElementById("presetLibraryList");
  const panelAutoEq = document.getElementById("autoEqPanel");
  const lblCategory = document.getElementById("lblSubTabCategory");
  const lblTitle = document.getElementById("lblSubTabTitle");

  if (tab === "presets") {
    btnPresets.classList.add("active");
    btnAutoEq.classList.remove("active");
    listPresets.style.display = "flex";
    panelAutoEq.classList.remove("active");
    lblCategory.textContent = "DSP ACOUSTIC LIBRARY";
    lblTitle.textContent = "Perfis & Presets";
  } else {
    btnPresets.classList.remove("active");
    btnAutoEq.classList.add("active");
    listPresets.style.display = "none";
    panelAutoEq.classList.add("active");
    lblCategory.textContent = "AUTOEQ™ HARMAN DATABASE";
    lblTitle.textContent = "Calibração de Fones";
    if (!autoEqCache.length) {
      fetchAutoEqData();
    }
  }
}

function fetchAutoEqData() {
  if (window.pywebview && window.pywebview.api && window.pywebview.api.search_autoeq_profiles) {
    window.pywebview.api.search_autoeq_profiles(autoEqSearchQuery, currentAutoEqBrand).then((items) => {
      autoEqCache = items || [];
      renderAutoEqList(autoEqCache);
    });
  } else {
    const q = autoEqSearchQuery.toLowerCase();
    const filtered = LOCAL_AUTOEQ_FALLBACK.filter((it) => {
      const matchBrand = currentAutoEqBrand === "all" || it.brand.toLowerCase() === currentAutoEqBrand.toLowerCase();
      const matchQ = !q || (it.name + " " + it.brand + " " + it.desc).toLowerCase().includes(q);
      return matchBrand && matchQ;
    });
    renderAutoEqList(filtered);
  }
}

function selectAutoEqBrand(brand, btnEl) {
  currentAutoEqBrand = brand;
  document.querySelectorAll(".autoeq-brand-pills .brand-pill").forEach((b) => b.classList.remove("active"));
  if (btnEl) btnEl.classList.add("active");
  fetchAutoEqData();
}

let autoEqSearchDebounce = null;
function onAutoEqSearch(val) {
  autoEqSearchQuery = val;
  if (autoEqSearchDebounce) clearTimeout(autoEqSearchDebounce);
  autoEqSearchDebounce = setTimeout(() => {
    fetchAutoEqData();
  }, 150);
}

function clearAutoEqSearch() {
  const inp = document.getElementById("inpAutoEqSearch");
  if (inp) inp.value = "";
  autoEqSearchQuery = "";
  fetchAutoEqData();
}

function renderAutoEqList(items) {
  const list = document.getElementById("autoEqResultsList");
  if (!list) return;

  if (!items || items.length === 0) {
    list.innerHTML = `<div style="text-align: center; padding: 24px 10px; color: var(--text-muted); font-size: 0.74rem;">
      Nenhum fone encontrado para "<strong>${autoEqSearchQuery}</strong>".<br>Experimente buscar por Sony, AirPods ou Buds.
    </div>`;
    return;
  }

  let html = "";
  items.forEach((item) => {
    const cbText = (item.clear_bass >= 0 ? "+" + item.clear_bass : item.clear_bass) + " dB";
    const bandsText = item.bands.map((b) => (b >= 0 ? "+" + b : b)).join(" ");
    const safeItemJson = JSON.stringify(item).replace(/'/g, "&apos;");
    html += `
      <div class="autoeq-card" onclick='applyAutoEqItem(${safeItemJson})' title="Clique para aplicar a calibração de ${item.name}">
        <div class="autoeq-top-row">
          <span class="autoeq-phone-title">${item.name}</span>
          <span class="autoeq-target-badge">${item.brand}</span>
        </div>
        <div class="autoeq-bands-preview">
          CB: ${cbText} • [${bandsText}]
        </div>
        <div class="autoeq-desc">${item.desc}</div>
      </div>
    `;
  });
  list.innerHTML = html;
}

function applyAutoEqItem(item) {
  if (!item) return;
  eqTarget = [item.clear_bass, ...item.bands];
  startEqSpring();
  setActivePresetUI(`AutoEq: ${item.name}`);

  if (window.pywebview && window.pywebview.api && window.pywebview.api.apply_autoeq_profile) {
    window.pywebview.api.apply_autoeq_profile(item.name, item.clear_bass, item.bands);
  }
  window.showToast && window.showToast(`Calibração AutoEq: ${item.name}`, "🎯");
}
