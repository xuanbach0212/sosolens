from backend.agent.detectors.etf_flow_spike import ETFFlowSpikeDetector

DETECTORS: list = [ETFFlowSpikeDetector()]


def register(detector):
    DETECTORS.append(detector)
    return detector
