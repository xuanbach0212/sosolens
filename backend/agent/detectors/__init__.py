from backend.agent.detectors.etf_flow_spike import ETFFlowSpikeDetector
from backend.agent.detectors.sector_rotation import SectorRotationDetector

DETECTORS: list = [ETFFlowSpikeDetector(), SectorRotationDetector()]


def register(detector):
    DETECTORS.append(detector)
    return detector
