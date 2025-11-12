"""Demo rápido de parsers y estructuras de datos del proyecto.
Este script muestra cómo se ven las respuestas parseadas sin usar BLE.
"""
from datetime import datetime, timezone

from colmi_r02_client import battery, real_time, hr, steps, packet, pretty_print


def demo_battery():
    # ejemplo inspirado en la docstring de battery.parse_battery
    p = bytearray(16)
    p[0] = battery.CMD_BATTERY
    p[1] = 64  # nivel de bateria
    p[2] = 0   # charging flag
    p[-1] = packet.checksum(p)
    print("Battery packet:", p)
    bi = battery.parse_battery(p)
    print("Parsed battery:", bi)


def demo_realtime():
    # ejemplo de lectura real time (heart rate)
    p = bytearray(16)
    p[0] = real_time.CMD_START_REAL_TIME
    p[1] = real_time.RealTimeReading.HEART_RATE
    p[2] = 0  # error code
    p[3] = 81  # value
    p[-1] = packet.checksum(p)
    print("Real-time packet:", p)
    r = real_time.parse_real_time_reading(p)
    print("Parsed real-time:", r)


def demo_hr_nodata():
    # forzar NoData usando subtype 255
    p = bytearray(16)
    p[0] = hr.CMD_READ_HEART_RATE
    p[1] = 255
    p[-1] = packet.checksum(p)
    print("HR NoData packet:", p)
    res = hr.HeartRateLogParser().parse(p)
    print("Parsed HR result:", type(res), res)


def demo_steps_nodata():
    p = bytearray(16)
    p[0] = steps.CMD_GET_STEP_SOMEDAY
    p[1] = 255
    p[-1] = packet.checksum(p)
    print("Steps NoData packet:", p)
    res = steps.SportDetailParser().parse(p)
    print("Parsed steps result:", type(res), res)


def demo_make_packet():
    sub = bytearray(b"\x01\x02\x03")
    p = packet.make_packet(10, sub)
    print("make_packet(10,[1,2,3]) ->", p)
    print("checksum:", packet.checksum(p))


if __name__ == '__main__':
    print("Demo parsers and data shapes:\n")
    demo_battery()
    print()
    demo_realtime()
    print()
    demo_hr_nodata()
    print()
    demo_steps_nodata()
    print()
    demo_make_packet()
    print("\nFinished demo at", datetime.now(timezone.utc).isoformat())
