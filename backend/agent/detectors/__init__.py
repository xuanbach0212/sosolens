DETECTORS: list = []


def register(detector):
    """Decorator/function to register a signal detector. Used by #11, #12, #13."""
    DETECTORS.append(detector)
    return detector
