# huawei_solar_modbus_mqtt/bridge/cache_layer.py


"""
Cache-Layer für stabilisierte MQTT-Publishes zwischen zwei Modbus-Poll-Zyklen.

Der Huawei Inverter erlaubt aus Stabilitätsgründen nur relativ langsames
Polling (typisch 20 bis 30 Sekunden). Einige Verbraucher wie EVCC erwarten jedoch
häufigere Updates der Leistungswerte, um ihre Regelalgorithmen stabil zu
halten.

Dieser Cache speichert den zuletzt erfolgreich publizierten MQTT-Payload
vollständig und stellt ihn zwischen zwei echten Modbus-Lesezyklen erneut
zur Verfügung. Dadurch bleiben alle Home Assistant Sensoren stabil — es
entstehen keine unvollständigen Payloads und keine "unknown"-Zustände.

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
    CacheLayer.get_cached() → MQTT publish (gecachte Daten)

Wichtige Eigenschaften:
  - vollständig optional (aktivierbar über enable_caching)
  - verändert keine Datenlogik
  - speichert immer den kompletten Payload, nie einzelne Keys
  - verhindert "unknown"-Zustände bei langsamen Poll-Intervallen
  - schützt durch max_age vor veralteten Daten
"""

import time
from typing import Any


class CacheLayer:
    """
    Einfacher In-Memory Cache für vollständige MQTT-Payloads.

    Speichert den letzten vollständigen MQTT-Payload zusammen mit einem
    Zeitstempel und stellt ihn bis zu einer maximalen Lebensdauer
    (`max_age`) wieder zur Verfügung.

    Wichtig: Der gesamte Payload wird atomar gespeichert und zurückgegeben.
    Es werden keine einzelnen Keys mit separaten Zeitstempeln verwaltet —
    dadurch ist der Payload immer vollständig oder gar nicht vorhanden.

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
                Maximales Alter des gecachten Payloads in Sekunden.
                Payloads, die älter sind, werden nicht mehr zurückgegeben.
        """
        self.enabled = enabled
        self.max_age = max_age
        self._payload: dict[str, Any] | None = None
        self._timestamp: float = 0

    @property
    def is_valid(self) -> bool:
        """True wenn Cache einen vollständigen Payload enthält und nicht abgelaufen ist."""
        return bool(self._payload) and (time.time() - self._timestamp <= self.max_age)

    def update(self, data: dict[str, Any]) -> None:
        """
        Aktualisiert den Cache mit einem neuen vollständigen MQTT-Payload.

        Der gesamte Payload wird als Einheit gespeichert. Dadurch ist
        sichergestellt, dass bei einem späteren get_cached() immer ein
        vollständiger Payload zurückgegeben wird.

        Args:
            data:
                Vollständiges MQTT-Daten-Dictionary aus dem Transform-/Filter-Schritt.
        """
        if not self.enabled:
            return
        self._payload = data.copy()
        self._timestamp = time.time()

    def get_cached(self) -> dict[str, Any]:
        """
        Gibt den gecachten Payload zurück, wenn er noch gültig ist.

        Der Payload wird nur zurückgegeben, wenn sein Alter `max_age`
        nicht überschreitet. Da immer der vollständige Payload gespeichert
        wird, enthält das Ergebnis alle Keys — oder ist leer.

        Returns:
            Vollständiges Dictionary mit gecachten MQTT-Daten.
            Leer wenn der Cache deaktiviert ist, noch nie befüllt wurde
            oder der Payload abgelaufen ist.
        """
        if not self.enabled or not self._payload:
            return {}
        if time.time() - self._timestamp > self.max_age:
            return {}
        return self._payload
