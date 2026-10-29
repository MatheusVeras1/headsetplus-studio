# -*- coding: utf-8 -*-
import sys
import os
import json
import re

sys.stdout.reconfigure(encoding='utf-8')

print("1. Testando detecção do idioma do sistema operacional...")
sys.path.insert(0, os.path.abspath("."))
import importlib.util
spec = importlib.util.spec_from_file_location("headsetplus_studio", "headsetplus_studio.pyw")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
detect_system_language = mod.detect_system_language
load_config = mod.load_config
sys_lang = detect_system_language()
print(f"   Idioma detectado do Windows: {sys_lang}")
assert sys_lang in ['pt-BR', 'en-US', 'ja-JP', 'es-ES', 'de-DE', 'zh-CN', 'fr-FR'], f"Idioma inválido: {sys_lang}"

print("\n2. Testando bootstrap com idioma do sistema...")
cfg = load_config()
print(f"   Config loaded language: {cfg.get('language')}")
assert "language" in cfg

print("\n3. Verificando cobertura do ui_ghub.html e ui/i18n.js...")
with open("ui_ghub.html", "r", encoding="utf-8") as f:
    html = f.read()

with open("ui/i18n.js", "r", encoding="utf-8") as f:
    js = f.read()

m = re.search(r'const I18N_TRANSLATIONS = (\{[\s\S]*?\n\});', js)
assert m, "I18N_TRANSLATIONS não encontrado"
translations = json.loads(m.group(1))

# Chaves essenciais que o usuário mencionou especificamente:
# 1. Ambos os fones e estojo (hero deck)
assert "hero.left" in html
assert "hero.case" in html
assert "hero.right" in html
assert "hero.master" in html
assert "hero.sync" in html
assert "hero.case_charge" in html

# 2. Todas as abas
assert "eq.engine_title" in html
assert "nc.chip_label" in html
assert "hw.micro" in html
assert "shield.shield_micro" in html
assert "spatial.stage_micro" in html
assert "settings.micro" in html

# 3. Testando traduções em cada um dos 7 idiomas
for lang in ['pt-BR', 'en-US', 'ja-JP', 'es-ES', 'de-DE', 'zh-CN', 'fr-FR']:
    t = translations[lang]
    assert t["hero"]["left"], f"hero.left vazio para {lang}"
    assert t["hero"]["case"], f"hero.case vazio para {lang}"
    assert t["hero"]["right"], f"hero.right vazio para {lang}"
    print(f"   [{lang}] L: '{t['hero']['left']}' | Case: '{t['hero']['case']}' | R: '{t['hero']['right']}'")

print("\n4. Verificando renderDeviceSelectorItems e connTxt em ui/app.js...")
with open("ui/app.js", "r", encoding="utf-8") as f:
    app_js = f.read()

assert 'window.getTranslation("header.device_select_header")' in app_js
assert 'window.getTranslation("header.connected")' in app_js
assert 'window.getTranslation("header.disconnected")' in app_js
assert 'window.getTranslation("hero.charging")' in app_js
print("   ui/app.js devidamente internacionalizado para elementos dinâmicos!")

print("\n🎉 TODOS OS TESTES DE INTERNACIONALIZAÇÃO (i18n) E DETECÇÃO DE SISTEMA FORAM APROVADOS!")
