# tests\test_cache_layer.py

"""Tests for Cache Layer."""

import time

from huawei_solar_modbus_mqtt.bridge.cache_layer import CacheLayer


def test_cache_disabled_returns_empty():
    """Cache sollte nichts zurückgeben wenn deaktiviert."""
    cache = CacheLayer(enabled=False)
    cache.update({"power": 100})
    print(type(cache))

    assert cache.get_cached() == {}


def test_cache_update_returns_none():
    """update() sollte None zurückgeben."""
    cache = CacheLayer(enabled=True)
    cache.update({"power": 100})
    result = cache.get_cached()
    assert "power" in result
    assert result["power"] == 100


def test_cache_update_and_get():
    """Gespeicherte Werte sollten wieder abrufbar sein."""
    cache = CacheLayer(enabled=True, max_age=30)
    data = {
        "power_input": 500,
        "battery_power": -200,
    }

    cache.update(data)
    result = cache.get_cached()

    assert result == data


def test_cache_update_empty_data():
    """update() mit leerem Dict sollte keinen Fehler werfen."""
    cache = CacheLayer(enabled=True)
    cache.update({})

    assert cache.get_cached() == {}


def test_cache_update_overwrites_existing():
    """Neuere Werte sollen ältere überschreiben."""
    cache = CacheLayer(enabled=True, max_age=30)
    cache.update({"power": 100})
    cache.update({"power": 200})

    assert cache.get_cached()["power"] == 200


def test_cache_ignores_non_numeric_values():
    """Nur numerische Werte sollen gecached werden."""
    cache = CacheLayer(enabled=True)
    cache.update(
        {
            "power": 100,
            "status": "online",
            "mode": None,
        }
    )
    result = cache.get_cached()

    assert result == {"power": 100}


def test_cache_respects_max_age():
    """Cache sollte Werte verwerfen wenn max_age überschritten ist."""
    cache = CacheLayer(enabled=True, max_age=1)
    cache.update({"power": 100})
    time.sleep(1.5)

    result = cache.get_cached()

    assert result == {}


def test_cache_partial_expiry():
    """Einträge mit unterschiedlichen Zeitstempeln sollten korrekt gefiltert werden."""
    cache = CacheLayer(enabled=True, max_age=2)
    cache.update({"power": 100})
    time.sleep(1)
    cache.update({"battery": 50})
    result = cache.get_cached()

    # Beide noch gültig
    assert result["power"] == 100
    assert result["battery"] == 50


def test_cache_get_empty():
    """get_cached() auf frischem Cache gibt leeres Dict zurück."""
    cache = CacheLayer(enabled=True)
    assert cache.get_cached() == {}


def test_cache_partial_expiry_precise():
    """Abgelaufene Einträge werden gefiltert, frische nicht."""
    cache = CacheLayer(enabled=True, max_age=2)

    # power: alt (3s) → abgelaufen
    cache._cache["power"] = (100, time.time() - 3)
    # battery: frisch → gültig
    cache._cache["battery"] = (50, time.time())

    result = cache.get_cached()

    assert "power" not in result
    assert result["battery"] == 50
