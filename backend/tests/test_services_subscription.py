"""Tests for subscription.py — no contract or RPC required (mocks web3)."""
import time
from unittest.mock import MagicMock, patch

import pytest

WALLET = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
WALLET_CS = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"


def _make_contract(subscribed: bool, expiry: int = 0):
    contract = MagicMock()
    contract.functions.isSubscribed.return_value.call.return_value = subscribed
    contract.functions.subscriptionExpiry.return_value.call.return_value = expiry
    return contract


@pytest.fixture(autouse=True)
def clear_cache():
    from backend.services import subscription as sub_module
    sub_module._cache.clear()
    sub_module._contract = None
    yield
    sub_module._cache.clear()
    sub_module._contract = None


def test_is_subscribed_returns_false_when_no_contract_address():
    with patch.dict("os.environ", {"SUBSCRIPTION_CONTRACT_ADDRESS": ""}):
        from backend.services import subscription as sub_module
        sub_module._CONTRACT_ADDRESS = ""
        result = sub_module.is_subscribed(WALLET)
    assert result is False


def test_is_subscribed_returns_true_when_subscribed():
    contract = _make_contract(subscribed=True, expiry=int(time.time()) + 86400)
    from backend.services import subscription as sub_module
    sub_module._CONTRACT_ADDRESS = "0x1234"
    with patch.object(sub_module, "_get_contract", return_value=contract):
        result = sub_module.is_subscribed(WALLET)
    assert result is True


def test_is_subscribed_returns_false_when_not_subscribed():
    contract = _make_contract(subscribed=False)
    from backend.services import subscription as sub_module
    sub_module._CONTRACT_ADDRESS = "0x1234"
    with patch.object(sub_module, "_get_contract", return_value=contract):
        result = sub_module.is_subscribed(WALLET)
    assert result is False


def test_is_subscribed_uses_cache():
    contract = _make_contract(subscribed=True)
    from backend.services import subscription as sub_module
    sub_module._CONTRACT_ADDRESS = "0x1234"
    with patch.object(sub_module, "_get_contract", return_value=contract):
        sub_module.is_subscribed(WALLET)
        sub_module.is_subscribed(WALLET)
    # contract called only once; second call hit cache
    assert contract.functions.isSubscribed.call_count == 1


def test_is_subscribed_returns_false_on_rpc_error():
    from backend.services import subscription as sub_module
    sub_module._CONTRACT_ADDRESS = "0x1234"
    with patch.object(sub_module, "_get_contract", side_effect=Exception("RPC down")):
        result = sub_module.is_subscribed(WALLET)
    assert result is False


def test_get_expiry_returns_none_when_no_contract():
    from backend.services import subscription as sub_module
    sub_module._CONTRACT_ADDRESS = ""
    result = sub_module.get_expiry(WALLET)
    assert result is None


def test_get_expiry_returns_timestamp():
    expiry = int(time.time()) + 86400
    contract = _make_contract(subscribed=True, expiry=expiry)
    from backend.services import subscription as sub_module
    sub_module._CONTRACT_ADDRESS = "0x1234"
    with patch.object(sub_module, "_get_contract", return_value=contract):
        result = sub_module.get_expiry(WALLET)
    assert result == expiry
