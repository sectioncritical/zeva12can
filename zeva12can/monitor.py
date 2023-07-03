import zeva12can
import can

def cli():

    print("Initializing CAN bus")
    bus = can.interface.Bus(bustype="socketcan", channel="can0", bitrate=250000)

    units = []
    for unit in range(16):
        print(f"Probing unit {unit} ... ", end="")
        bmsunit = zeva12can.BMS12(unit=unit, canbus=bus)
        ver = bmsunit.probe()
        if ver:
            print(f"{ver[0]}.{ver[1]}.{ver[2]}")
            units += [bmsunit]
        else:
            print()

    for unit in units:
        unit.update()
        print(f"[{unit.unit:2d}] ", end="")
        for mv in unit.cellmv:
            print(f"{mv:5d} ", end="")
        print()


if __name__ == "__main__":
    cli()
