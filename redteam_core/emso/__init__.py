"""emso — 전자전(EMSO) 정박 (고도화 §C, JP 3-85 JEMSO).

동언님 jam·gnss_spoof 는 코어에서 '사이버 액션'으로만 취급되고 실링크에선
NotImplementedError 였다. 교리상 이건 **전자공격(EA, Electronic Attack)** 이다.
이 패키지는 그 물리효과를 결정론으로 모델링한다 — blue counter-uas 의 RF 모델
(log-distance 경로손실·J/S)과 **대칭**이라 물리적으로 정합적이다.

교리 근거:
  - JP 3-85 (JEMSO): EW = EA(방해·기만)·ES·EP. 스펙트럼 데컨플릭션(JCEOI).
  - §B RoE 게이트가 EA 방사 전 JCEOI 승인을 강제(fail-safe).
  - 산출 효과는 §A BDA 로 연결: gnss_spoof → PosHorizVariance 강도 → blue S1.
"""
from .rf import BANDS, Band, band_for, j_to_s_db, path_loss_db, rssi_dbm
from .effects import EwEffect, gnss_spoof_effect, jam_effect
from .engage import EmsoOutcome, plan_emso

__all__ = [
    "BANDS", "Band", "band_for", "j_to_s_db", "path_loss_db", "rssi_dbm",
    "EwEffect", "gnss_spoof_effect", "jam_effect",
    "EmsoOutcome", "plan_emso",
]
