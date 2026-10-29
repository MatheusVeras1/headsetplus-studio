# -*- coding: utf-8 -*-
with open('ui_ghub.html', 'r', encoding='utf-8') as f:
    text = f.read()

repls = [
    ('<span class="micro-label" data-i18n="settings.alerts_title">ALERTAS & SAÚDE AUDITIVA</span>\n              <h2 class="section-title" style="font-size: 0.98rem;">Monitoramento & Notificações</h2>',
     '<span class="micro-label" data-i18n="settings.alerts_micro">ALERTAS & SAÚDE AUDITIVA</span>\n              <h2 class="section-title" data-i18n="settings.alerts_title" style="font-size: 0.98rem;">Monitoramento & Notificações</h2>'),
    ('<button class="btn" style="padding: 6px 12px; font-size: 0.74rem;" onclick="replaySplash()">\n                ▶️ Reproduzir\n              </button>',
     '<button class="btn" style="padding: 6px 12px; font-size: 0.74rem;" onclick="replaySplash()" data-i18n="settings.replay_btn">\n                ▶️ Reproduzir\n              </button>'),
    ('<!-- COMPORTAMENTO WINDOWS 11 -->\n            <div style="display: flex; flex-direction: column; gap: 8px;">',
     '<!-- COMPORTAMENTO WINDOWS 11 -->\n            <div class="micro-label" data-i18n="settings.sys_title" style="margin-top: 10px; margin-bottom: 2px;">COMPORTAMENTO NO WINDOWS 11</div>\n            <div style="display: flex; flex-direction: column; gap: 8px;">')
]

for old, new in repls:
    if old in text:
        text = text.replace(old, new, 1)
        print("Replaced:", old[:30])
    else:
        print("Not found:", repr(old[:30]))

with open('ui_ghub.html', 'w', encoding='utf-8') as f:
    f.write(text)
