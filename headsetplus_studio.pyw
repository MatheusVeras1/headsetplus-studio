# -*- coding: utf-8 -*-
"""
HeadsetPlus Studio — Ponto de Entrada Oficial
Created by Matheus Veras • Licença: Source-Available Proprietary (Ver LICENSE.md)

Suíte de Controle Acústico Universal, DSP Paramétrico Global Windows 11 & Ecossistema Multimarca.
"""

from sony_sound_connect_pc import (
    SonyGHubController,
    acquire_single_instance_lock,
    main,
)

if __name__ == "__main__":
    main()
