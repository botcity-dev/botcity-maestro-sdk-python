import pytest
from botcity.maestro import BotMaestroSDK

def test_items_all_none():
    sdk = BotMaestroSDK()
    total, processed, failed = sdk._validate_items(None, None, None)
    assert total is None
    assert processed is None
    assert failed is None

def test_items_total_none():
    sdk = BotMaestroSDK()
    total, processed, failed = sdk._validate_items(None, 5, 5)
    assert total == 10
    assert processed == 5
    assert failed == 5

def test_items_failed_none():
    sdk = BotMaestroSDK()
    total, processed, failed = sdk._validate_items(10, 5, None)
    assert total == 10
    assert processed == 5
    assert failed == 5

def test_items_processed_none():
    sdk = BotMaestroSDK()
    total, processed, failed = sdk._validate_items(10, None, 5)
    assert total == 10
    assert processed == 5
    assert failed == 5

def test_items_no_negative_values():
    sdk = BotMaestroSDK()
    total, processed, failed = sdk._validate_items(-10, -5, -5)
    assert total == 0
    assert processed == 0
    assert failed == 0

def test_items_total_not_equal_to_sum():
    sdk = BotMaestroSDK()
    with pytest.raises(ValueError):
        sdk._validate_items(10, 5, 6)