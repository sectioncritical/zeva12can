import sys
import zeva12can
import can

def cli():

    if len(sys.argv) != 2:
        print("usage: reboot <id>")
        print("  where <id> is 0-15")
        return

    unit = int(sys.argv[1])
    print(f"Attempt to reboot unit {unit}")
    print("Initializing CAN bus")
    bus = can.interface.Bus(bustype="socketcan", channel="can0", bitrate=250000)
    bmsunit = zeva12can.BMS12(unit=unit, canbus=bus)
    ok = bmsunit.reboot()
    if ok:
        print(f"Unit {unit} acknowledges reboot request")
    else:
        print("no reply")


if __name__ == "__main__":
    cli()
