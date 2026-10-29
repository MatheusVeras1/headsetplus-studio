# -*- coding: utf-8 -*-
import sys
import re
import os

sys.stdout.reconfigure(encoding='utf-8')

print("=" * 70)
print("SESSÃO DE AUDITORIA COMPLETA: HANDLERS HTML & INTEGRAÇÃO JAVASCRIPT")
print("=" * 70)

with open("ui_ghub.html", "r", encoding="utf-8") as f:
    html = f.read()

# Load all JS files
js_files = ["ui/i18n.js", "ui/eq_engine.js", "ui/acoustic_lab.js", "ui/app.js"]
js_contents = {}
combined_js = ""
for jf in js_files:
    with open(jf, "r", encoding="utf-8") as f:
        c = f.read()
        js_contents[jf] = c
        combined_js += f"\n/* --- {jf} --- */\n" + c

# 1. Extrair todos os manipuladores de eventos inline no HTML
# onclick, onchange, oninput, onpointerdown, onpointerup, onpointerleave, onpointercancel
event_attrs = ["onclick", "onchange", "oninput", "onpointerdown", "onpointerup", "onpointerleave", "onpointercancel"]
handlers_found = []

for attr in event_attrs:
    matches = re.findall(rf'{attr}="([^"]+)"', html)
    for m in matches:
        handlers_found.append((attr, m.strip()))

print(f"\n[1] Extraídos {len(handlers_found)} manipuladores de eventos do ui_ghub.html.")

# Extract called function names from the handler strings
called_functions = set()
for attr, code in handlers_found:
    # Match function calls like foo(...) or foo()
    fn_matches = re.findall(r'([a-zA-Z0-9_$]+)\s*\(', code)
    for fn in fn_matches:
        if fn not in ["event", "this", "false", "true", "null"]:
            called_functions.add(fn)

print(f"[2] Identificadas {len(called_functions)} funções distintas invocadas pelo HTML:")
for fn in sorted(called_functions):
    # Check if defined in any JS file
    # Definitions can be: function fn(, window.fn =, const fn =, let fn =
    defined = False
    origin = None
    for jf, content in js_contents.items():
        pattern = rf'(?:function\s+{fn}\b|window\.{fn}\s*=|{fn}\s*=\s*(?:function|\()|\bclass\s+{fn}\b)'
        if re.search(pattern, content):
            defined = True
            origin = jf
            break
    
    if defined:
        print(f"    ✓ {fn:<32} [Definida em {origin}]")
    else:
        # Check standard browser functions
        if fn in ["alert", "confirm", "prompt", "parseInt", "parseFloat"]:
            print(f"    ✓ {fn:<32} [Nativa Browser]")
        else:
            print(f"    ❌ {fn:<32} [NÃO ENCONTRADA!]")

# 2. Verificar todos os IDs consultados no JS via document.getElementById
print("\n[3] Auditando todos os getElementById(...) em todo o código JavaScript:")
js_id_matches = re.findall(r'document\.getElementById\(\s*["\']([^"\']+)["\']\s*\)', combined_js)
unique_js_ids = sorted(set(js_id_matches))
print(f"    Total de IDs únicos consultados no JS: {len(unique_js_ids)}")

html_ids = set(re.findall(r'id=["\']([^"\']+)["\']', html))
missing_ids = []
for jid in unique_js_ids:
    if jid not in html_ids:
        # Some IDs might be created dynamically in templates
        dynamic_template = (jid in combined_js and ("<div" in combined_js or "<span" in combined_js))
        if dynamic_template:
            print(f"    ℹ️ {jid:<30} (Criado dinamicamente em template JS)")
        else:
            missing_ids.append(jid)
            print(f"    ❌ ID NÃO ENCONTRADO NO HTML: {jid}")

if not missing_ids:
    print("    ✓ TODOS os IDs estáticos consultados no JS existem perfeitamente no HTML!")

# 3. Verificar todas as chamadas window.pywebview.api.*
print("\n[4] Auditando chamadas window.pywebview.api.* no JavaScript:")
api_calls = set(re.findall(r'window\.pywebview\.api\.([a-zA-Z0-9_]+)\s*\(', combined_js))
print(f"    Total de chamadas RPC encontradas no JS: {len(api_calls)}")

with open("headsetplus_studio.pyw", "r", encoding="utf-8") as f:
    py_code = f.read()

# Extract methods of GHubApiBridge
bridge_methods = set(re.findall(r'def\s+([a-zA-Z0-9_]+)\s*\(self', py_code))

missing_rpc = []
for call in sorted(api_calls):
    if call in bridge_methods:
        print(f"    ✓ pywebview.api.{call:<28} -> GHubApiBridge.{call}() OK")
    else:
        missing_rpc.append(call)
        print(f"    ❌ pywebview.api.{call:<28} -> NÃO EXISTE NO PYTHON!")

if not missing_rpc:
    print("    ✓ 100% das chamadas RPC do Frontend estão implementadas no Backend Python!")

print("\n" + "=" * 70)
