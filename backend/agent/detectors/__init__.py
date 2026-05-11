from backend.agent.detectors.etf_flow_spike import ETFFlowSpikeDetector
from backend.agent.detectors.sector_rotation import SectorRotationDetector
from backend.agent.detectors.macro_risk import MacroRiskDetector

DETECTORS: list = [ETFFlowSpikeDetector(), SectorRotationDetector(), MacroRiskDetector()]


def register(detector):
    DETECTORS.append(detector)
    return detector
