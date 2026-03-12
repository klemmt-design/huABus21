# tests/test_cache_layer.py

"""Tests for Cache Layer."""

import time

from huawei_solar_modbus_mqtt.bridge.cache_layer import CacheLayer


def test_cache_disabled_returns_empty():
    """Cache sollte nichts zurückgeben wenn deaktiviert."""
    cache = CacheLayer(enabled=False)
    cache.update({"power": 100})

    assert cache.get_cached() == {}


def test_cache_update_and_get():
    """Gespeicherte Werte sollten vollständig wieder abrufbar sein."""
    cache = CacheLayer(enabled=True, max_age=30)
    data = {
        "power_input": 500,
        "battery_power": -200,
    }

    cache.update(data)
    result = cache.get_cached()

    assert result == data


def test_cache_update_empty_data():
    """update() mit leerem Dict sollte leeres Dict zurückgeben."""
    cache = CacheLayer(enabled=True)
    cache.update({})

    assert cache.get_cached() == {}


def test_cache_update_overwrites_existing():
    """Neuerer Payload soll älteren komplett ersetzen."""
    cache = CacheLayer(enabled=True, max_age=30)
    cache.update({"power": 100})
    cache.update({"power": 200})

    assert cache.get_cached()["power"] == 200


def test_cache_stores_all_value_types():
    """Alle Werttypen (numerisch, string, None) sollen gecached werden."""
    cache = CacheLayer(enabled=True)
    data = {
        "power": 100,
        "status": "online",
        "mode": None,
    }
    cache.update(data)
    result = cache.get_cached()

    assert result == data


def test_cache_respects_max_age():
    """Cache sollte Payload verwerfen wenn max_age überschritten ist."""
    cache = CacheLayer(enabled=True, max_age=1)
    cache.update({"power": 100})
    time.sleep(1.5)

    assert cache.get_cached() == {}


def test_cache_get_empty():
    """get_cached() auf frischem Cache gibt leeres Dict zurück."""
    cache = CacheLayer(enabled=True)

    assert cache.get_cached() == {}


def test_cache_is_valid_false_when_empty():
    """is_valid sollte False sein wenn Cache leer ist."""
    cache = CacheLayer(enabled=True)

    assert cache.is_valid is False


def test_cache_is_valid_true_after_update():
    """is_valid sollte True sein nach erfolgreichem update()."""
    cache = CacheLayer(enabled=True, max_age=30)
    cache.update({"power": 100})

    assert cache.is_valid is True


def test_cache_is_valid_false_after_expiry():
    """is_valid sollte False sein wenn max_age abgelaufen ist."""
    cache = CacheLayer(enabled=True, max_age=1)
    cache.update({"power": 100})
    time.sleep(1.5)

    assert cache.is_valid is False


def test_cache_payload_is_copy():
    """Nachträgliche Änderungen am Original-Dict sollen Cache nicht beeinflussen."""
    cache = CacheLayer(enabled=True, max_age=30)
    data = {"power": 100}
    cache.update(data)

    data["power"] = 999  # Original mutieren

    assert cache.get_cached()["power"] == 100
