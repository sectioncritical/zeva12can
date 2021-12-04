Monitor Utility for Zeva BMS12/24
=================================

This is a python utility that can read the status of Zeva BMS 12/24 systems
via CAN bus.

LICENSE
-------

This project uses the [MIT License](https://opensource.org/licenses/MIT).
See the [LICENSE.txt file](LICENSE.md) for the license terms.

About
-----

[ZEVA](https://www.zeva.com.au/index.php) makes battery management systems for
electric vehicles and other applications. The [BMS12](https://www.zeva.com.au/index.php?product=133)
and [BMS24](https://www.zeva.com.au/index.php?product=143) products communicate
via a CAN bus and use the same protocol. The protocol definition can be found
here: [ZEVA BMS12 CAN Protocol](https://www.zeva.com.au/Products/datasheets/BMS12v3_CAN_Protocol.pdf).

**TODO:** add protocol docs to this repo.

This program is a simple monitor utility that reads the status of any BMS units
on a CAN bus as displays as a simple text table. The package consists of a
command line utility and a module with a "BMS12" class that handles the message
protocol.

Hardware Requirements
---------------------

The computer that runs this program must have a CAN interface attached. This
program assumes a Raspberry Pi with an attached MCP2515-based CAN board. This
program can probably be modified to work with other CAN hardware setups. The
[bms12 module](zeva12can/bms12.py) is hardware independent as long as a
[python-can](https://python-can.readthedocs.io/en/master/) interface is
provided.

**TODO:** add hardware hookup and system config details

Installation
------------

**This package is not on pypi.**

You should be using a python virtual environment.

You can:

- install from github: `pip install git+https://github.com/sectioncritical/zeva12can.git`
- clone and install from file system: `pip install path/to/zeva12can`

Usage
-----

Once installed you can just run `monitor`. There are no command line arguments.
It scans the CAN bus for all available units (0-15) and then prints the voltage
status of any units found.

**TODO:** add options for continuous monitor, pretty display, temperature
sensors

Related Projects
----------------

This project was created as a result of ZEVA making their products open-source.
Other project related to this are:

- [CAN Boot Loader](https://github.com/sectioncritical/atmega_can_bootloader)
- [ZEVA BMS24 Firmware](https://github.com/sectioncritical/zeva24_firmware)
- [ZEVA BMS24 Board](https://github.com/sectioncritical/zeva24_board)

More details about the CAN configuration are provided in the Firmware project.
