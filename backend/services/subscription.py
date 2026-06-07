import os
import time
import logging
from web3 import Web3

logger = logging.getLogger(__name__)

_ABI = [
    {
        "inputs": [{"internalType": "address", "name": "subscriber", "type": "address"}],
        "name": "isSubscribed",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "address", "name": "", "type": "address"}],
        "name": "subscriptionExpiry",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
]

_RPC_URL = os.getenv("RPC_URL", "https://sepolia.base.org")
_CONTRACT_ADDRESS = os.getenv("SUBSCRIPTION_CONTRACT_ADDRESS", "")

_w3: Web3 | None = None
_contract = None
_cache: dict[str, tuple[bool, float]] = {}
_CACHE_TTL = 60.0


def _get_contract():
    global _w3, _contract
    if not _CONTRACT_ADDRESS:
        return None
    if _contract is None:
        _w3 = Web3(Web3.HTTPProvider(_RPC_URL))
        addr = Web3.to_checksum_address(_CONTRACT_ADDRESS)
        _contract = _w3.eth.contract(address=addr, abi=_ABI)
    return _contract


def is_subscribed(wallet: str) -> bool:
    """Return True if wallet has an active SoSoLens subscription. Cached 60s."""
    if not wallet or not _CONTRACT_ADDRESS:
        return False

    now = time.monotonic()
    cached = _cache.get(wallet)
    if cached and now - cached[1] < _CACHE_TTL:
        return cached[0]

    try:
        contract = _get_contract()
        if contract is None:
            return False
        checksum = Web3.to_checksum_address(wallet)
        result: bool = contract.functions.isSubscribed(checksum).call()
        _cache[wallet] = (result, now)
        return result
    except Exception as exc:
        logger.warning("subscription check failed for %s: %s", wallet, exc)
        return False


def get_expiry(wallet: str) -> int | None:
    """Return UNIX expiry timestamp for wallet, or None if contract unavailable."""
    if not wallet or not _CONTRACT_ADDRESS:
        return None
    try:
        contract = _get_contract()
        if contract is None:
            return None
        checksum = Web3.to_checksum_address(wallet)
        expiry: int = contract.functions.subscriptionExpiry(checksum).call()
        return expiry if expiry > 0 else None
    except Exception as exc:
        logger.warning("expiry lookup failed for %s: %s", wallet, exc)
        return None
