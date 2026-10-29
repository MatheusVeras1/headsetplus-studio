"""
Verificação da Detecção Real de Bluetooth do Windows e Eliminação de Falsos Positivos.
Autor: Matheus Veras
Licença: Source-Available Proprietary (Ver LICENSE.md)
"""
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from core.device_detector import is_windows_bluetooth_connected
from sony_sound_connect_pc import SonyGHubController, load_config

def main():
    mac = "14:3F:A6:5D:DF:D5"
    print(f"1. Consultando API Win32 BluetoothGetDeviceInfo para {mac}...")
    is_conn = is_windows_bluetooth_connected(mac, "WF-1000XM3")
    print(f"   Resultado fConnected retornado pelo Windows: {is_conn}")
    assert is_conn is False, "O fone está fisicamente desligado/no estojo, logo deve ser False!"

    print("2. Inicializando SonyGHubController em modo real...")
    ctrl = SonyGHubController(force_mock=False)
    print(f"   ctrl.client.mock_mode: {ctrl.client.mock_mode}")
    print(f"   ctrl.client.connected: {ctrl.client.connected}")
    assert ctrl.client.mock_mode is False
    assert ctrl.client.connected is False

    print("3. Testando tentativa de conexao (connect)...")
    ok = ctrl.client.connect()
    print(f"   Retorno de connect(): {ok}")
    print(f"   Driver state connected: {ctrl.client.state.get('connected')}")
    print(f"   Driver state bat_l: {ctrl.client.state.get('bat_l')}")
    print(f"   Driver state bat_r: {ctrl.client.state.get('bat_r')}")
    print(f"   Driver state bat_case: {ctrl.client.state.get('bat_case')}")
    assert ok is False
    assert ctrl.client.state.get("connected") is False
    assert ctrl.client.state.get("bat_l") == 0
    assert ctrl.client.state.get("bat_r") == 0
    assert ctrl.client.state.get("bat_case") == 0

    print("4. Verificando persistencia em config.json...")
    cfg = load_config()
    print(f"   mock_mode em config.json: {cfg.get('mock_mode')}")
    assert cfg.get("mock_mode") is False

    print("SUCCESS: Falsos positivos 100% eliminados com sucesso!")
    ctrl.quit_app()

if __name__ == "__main__":
    main()

