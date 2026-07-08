"""RF 물리 — blue counter-uas/rf.py 와 대칭(log-distance PL·RSSI·J/S).

전력 dBm, 이득 dBi, 주파수 MHz, 거리 m. red 의 EA 효과가 blue 의 탐지 물리와
같은 모델을 쓰므로 J/S·RSSI 판정이 상호 정합적이다.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

_C = 299_792_458.0


@dataclass(frozen=True)
class Band:
    name: str
    low_mhz: float
    high_mhz: float
    typical_use: str

    @property
    def center_mhz(self) -> float:
        return (self.low_mhz + self.high_mhz) / 2.0


# blue counter-uas 와 동일 대역 집합(+ GPS L1 항법 표적).
BANDS = (
    Band("433MHz", 433.0, 434.8, "장거리 텔레메트리"),
    Band("915MHz", 902.0, 928.0, "장거리 제어/텔레메트리"),
    Band("1.5GHz", 1574.0, 1577.0, "GPS L1(항법) — 스푸핑/재밍 표적"),
    Band("2.4GHz", 2400.0, 2483.5, "제어/조종(C2)"),
    Band("5.8GHz", 5725.0, 5875.0, "FPV 영상 다운링크"),
)


def band_for(freq_mhz: float):
    for b in BANDS:
        if b.low_mhz <= freq_mhz <= b.high_mhz:
            return b
    return None


def fspl_1m_db(freq_mhz: float) -> float:
    """1m 자유공간 경로손실(dB). = 20log10(f_MHz) - 27.55 근사."""
    return 20.0 * math.log10(freq_mhz) + 20.0 * math.log10(1e6) + \
        20.0 * math.log10(4.0 * math.pi / _C)


def path_loss_db(distance_m: float, freq_mhz: float, n: float = 2.2) -> float:
    d = max(distance_m, 1.0)
    return fspl_1m_db(freq_mhz) + 10.0 * n * math.log10(d)


def rssi_dbm(eirp_dbm: float, distance_m: float, freq_mhz: float,
             n: float = 2.2, rx_gain_dbi: float = 3.0) -> float:
    return eirp_dbm - path_loss_db(distance_m, freq_mhz, n) + rx_gain_dbi


def j_to_s_db(jammer_eirp_dbm: float, jammer_dist_m: float,
              signal_eirp_dbm: float, signal_dist_m: float,
              freq_mhz: float, n: float = 2.2) -> float:
    """표적 수신단 J/S(dB) = RSSI_jammer - RSSI_signal (같은 주파수·수신이득 상쇄)."""
    rj = rssi_dbm(jammer_eirp_dbm, jammer_dist_m, freq_mhz, n)
    rs = rssi_dbm(signal_eirp_dbm, signal_dist_m, freq_mhz, n)
    return rj - rs
