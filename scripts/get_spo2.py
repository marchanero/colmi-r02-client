"""Script sencillo para leer SPO2 en tiempo real desde la Colmi R02 y calcular estadísticos.

Uso:
    python scripts/get_spo2.py --address CB:2C:18:A7:4A:00

El script conecta al anillo, solicita lecturas SPO2 y recopila hasta N lecturas válidas
(o hasta un timeout máximo). Luego imprime lecturas crudas, media y mediana.
"""
import argparse
import asyncio
import statistics
from typing import List

from colmi_r02_client.client import Client
from colmi_r02_client import real_time


async def collect_spo2(address: str, count: int = 6, max_tries: int = 20, timeout: float = 2.0):
    """Conecta y colecciona hasta `count` lecturas válidas (no cero) de SPO2.
    Devuelve la lista de lecturas (puede ser vacía si hubo error).
    """
    readings: List[int] = []

    async with Client(address) as client:
        # Reusa la implementación del cliente para lecturas real-time
        result = await client.get_realtime_reading(real_time.RealTimeReading.SPO2)
        if result is None:
            return []
        # result es list[int]
        readings.extend(result)

    # Filtrar ceros y valores no razonables (ej. <50 o >100)
    valid = [r for r in readings if r and 50 <= r <= 100]
    return valid


def summarize(readings: List[int]):
    if not readings:
        print("No se obtuvieron lecturas válidas de SPO2")
        return
    mean = statistics.mean(readings)
    median = statistics.median(readings)
    minimum = min(readings)
    maximum = max(readings)
    print("SPO2 lecturas:", readings)
    print(f"N={len(readings)}  mean={mean:.1f}  median={median}  min={minimum}  max={maximum}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--address", required=True, help="MAC address del anillo")
    parser.add_argument("--count", type=int, default=6, help="Número de lecturas válidas a recolectar (por defecto 6)")
    args = parser.parse_args()

    address = args.address

    try:
        readings = asyncio.run(collect_spo2(address, count=args.count))
        summarize(readings)
    except Exception as e:
        print("Error al leer SPO2:", e)


if __name__ == '__main__':
    main()
