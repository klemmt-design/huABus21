# huawei_solar_modbus_mqtt\bridge\cache_layer.py

"""
Cache-Layer für stabilisierte MQTT-Publishes zwischen zwei Modbus-Poll-Zyklen.

Der Huawei Inverter erlaubt aus Stabilitätsgründen nur relativ langsames
Polling (typisch 20 bis 30 Sekunden). Einige Verbraucher wie EVCC erwarten jedoch
häufigere Updates der Leistungswerte, um ihre Regelalgorithmen stabil zu
halten.

Dieser Cache speichert die zuletzt erfolgreich publizierten MQTT-Daten und
stellt sie zwischen zwei echten Modbus-Lesezyklen erneut zur Verfügung.

Architektur:

    Modbus Read
        ↓
    transform_data()
        ↓
    TotalIncreasingFilter
        ↓
    MQTT publish (echte Daten)
        ↓
    CacheLayer.update()
        ↓
    sleep_until_next_poll()
        ↓
    CacheLayer.get() → MQTT publish (gecachte Daten)

Wichtige Eigenschaften:
  - vollständig optional (aktivierbar über enable_caching)
  - verändert keine Datenlogik
  - reduziert Null-Werte oder Datenlücken bei langsamen Poll-Intervallen
  - schützt durch max_age vor veralteten Daten
"""

import time
from typing import Any


class CacheLayer:
    """
    Einfacher In-Memory Cache für MQTT-Daten.

    Speichert numerische Sensorwerte zusammen mit einem Zeitstempel und stellt
    sie bis zu einer maximalen Lebensdauer (`max_age`) wieder zur Verfügung.

    Der Cache wird typischerweise nach jedem erfolgreichen Modbus-Zyklus
    aktualisiert und während der Sleep-Phase erneut publiziert.
    """

    def __init__(self, enabled: bool = False, max_age: int = 30):
        """
        Initialisiert den Cache.

        Args:
            enabled:
                Aktiviert oder deaktiviert den Cache komplett.

            max_age:
                Maximales Alter eines Cache-Wertes in Sekunden.
                Werte, die älter sind, werden nicht mehr zurückgegeben.
        """
        self.enabled = enabled
        self.max_age = max_age
        self._cache: dict[str, tuple[float, float]] = {}

    def update(self, data: dict[str, Any]) -> None:
        """
        Aktualisiert den Cache mit neuen Sensordaten.

        Jeder numerische Wert wird zusammen mit einem Zeitstempel gespeichert.

        Args:
            data:
                Dictionary mit MQTT-Daten aus dem Transform-/Filter-Schritt.
        """
        if not self.enabled:
            return
        now = time.time()
        for key, value in data.items():
            if isinstance(value, (int, float)):
                self._cache[key] = (value, now)

    def get_cached(self) -> dict[str, Any]:
        """
        Gibt alle noch gültigen Cache-Werte zurück.

        Werte werden nur zurückgegeben, wenn ihr Alter `max_age`
        nicht überschreitet.

        Returns:
            Dictionary mit gecachten Sensordaten.
            Kann leer sein, wenn der Cache deaktiviert ist oder
            keine gültigen Werte vorhanden sind.
        """
        if not self.enabled:
            return {}

        now = time.time()
        result = {}

        for key, (value, ts) in self._cache.items():
            if now - ts <= self.max_age:
                result[key] = value

        return result
