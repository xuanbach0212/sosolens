from backend.agent.detectors.etf_flow_spike import ETFFlowSpikeDetector
from backend.agent.detectors.sector_rotation import SectorRotationDetector
from backend.agent.detectors.macro_risk import MacroRiskDetector
from backend.agent.detectors.news_sentiment import NewsSentimentDetector
from backend.agent.detectors.btc_accumulation import BtcAccumulationDetector

DETECTORS: list = [ETFFlowSpikeDetector(), SectorRotationDetector(), MacroRiskDetector(), NewsSentimentDetector(), BtcAccumulationDetector()]


def register(detector):
    DETECTORS.append(detector)
    return detector
