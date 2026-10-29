"""
Fábrica & Registro de Drivers Multimarca — Sony Sound Connect PC
Autor: Matheus Veras
Licença: Source-Available Proprietary (Ver LICENSE.md)
"""

from typing import Any, Callable, Optional

from core.drivers.base import (
    AUTO_OFF_ID_TO_NAME,
    AUTO_OFF_OPTIONS,
    BaseHeadsetDriver,
    EQ_ID_TO_NAME,
    EQ_PRESETS,
    TOUCH_ID_TO_NAME,
    TOUCH_OPTIONS,
)
from core.drivers.sony_mdr_v1 import (
    SonyMdrClient,
    SonyMdrV1Driver,
    escape_specials,
    extract_mdr_frames,
    make_ack,
    make_packet,
    unescape_specials,
)
from core.drivers.sony_mdr_v2 import SonyMdrV2Driver
from core.drivers.universal_windows import UniversalWindowsDriver


def create_headset_driver(
    protocol: str = "sony_mdr",
    mac: str = "14:3F:A6:5D:DF:D5",
    port: int = 9,
    model_name: str = "WF-1000XM3",
    brand_name: str = "Sony",
    mock_mode: bool = False,
    apo_engine: Optional[Any] = None,
    on_state_update: Optional[Callable[[], None]] = None,
    on_status_msg: Optional[Callable[[str], None]] = None,
    on_wearing_event: Optional[Callable[[bool], None]] = None,
) -> BaseHeadsetDriver:
    """Instancia dinamicamente o driver adequado para o protocolo do fone selecionado."""
    proto = (protocol or "sony_mdr").strip().lower()
    if proto == "sony_mdr_v2":
        driver_cls = SonyMdrV2Driver
    elif proto in ("sony_mdr", "sony_v1"):
        driver_cls = SonyMdrV1Driver
    else:
        driver_cls = UniversalWindowsDriver

    return driver_cls(
        mac=mac,
        port=port,
        model_name=model_name,
        brand_name=brand_name,
        mock_mode=mock_mode,
        apo_engine=apo_engine,
        on_state_update=on_state_update,
        on_status_msg=on_status_msg,
        on_wearing_event=on_wearing_event,
    )


__all__ = [
    "AUTO_OFF_ID_TO_NAME",
    "AUTO_OFF_OPTIONS",
    "BaseHeadsetDriver",
    "EQ_ID_TO_NAME",
    "EQ_PRESETS",
    "SonyMdrClient",
    "SonyMdrV1Driver",
    "SonyMdrV2Driver",
    "TOUCH_ID_TO_NAME",
    "TOUCH_OPTIONS",
    "UniversalWindowsDriver",
    "create_headset_driver",
    "escape_specials",
    "extract_mdr_frames",
    "make_ack",
    "make_packet",
    "unescape_specials",
]
