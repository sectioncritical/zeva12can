import struct
import time
import can

class bms12(object):
    def __init__(self, unit, shuntmv=0, canbus=None):
        self._unit = unit
        self._shuntlvl = shuntmv
        self._bus = canbus
        self._cellmv = [0] * 12
        self._temps = [0, 0]

    @property
    def unit(self):
        return self._unit

    @property
    def shuntmv(self):
        return self._shuntlvl

    @shuntmv.setter
    def shuntmv(self, mv):
        self._shuntlvl = mv

    @property
    def canbus(self):
        return self._bus

    @canbus.setter
    def canbus(self, bus):
        self._bus = bus

    @property
    def cellmv(self):
        return self._cellmv

    @property
    def temperature(self):
        return self._temps

    def send_query(self):
        """Send query packet with shunt level to unit.

        Sends the query message to the unit. This also sets the shunt level.
        The shunt level should already be set using the `shuntmv` property.

        This function provides a brief delay after sending the message, then
        returns.

        """
        arbid = 300 + (self._unit * 10)
        payload = struct.pack(">H", self._shuntlvl)
        msg = can.Message(arbitration_id=arbid, is_extended_id=True, data=payload)
        self._bus.send(msg)

    def get_msgs(self):
        """Return a list of all pending received messsages.

        This function is used when it is expected that messages are received on
        the CAN bus (such as after a query). It will return a list of all
        received can messages. The list may be empty if there are no messages
        received.

        """
        msgs =[]
        while True:
            msg = self._bus.recv(timeout=0.1)
            if msg:
                msgs = msgs + [msg]
            else:
                break
        return msgs

    @staticmethod
    def unit_from_arbid(arbid):
        """Decode the unit number from an abritration ID.

        :param arbid: a CAN arbitration ID used for BMS communication
        :returns: the unit number or ``None`` if error

        """
        # valid range to get a reasonable unit number
        if arbid < 300 or arbid > 454:
            return None
        arbid -= 300
        arbid = int(arbid / 10)
        return arbid

    @staticmethod
    def type_from_arbid(arbid):
        """Decode the message type from the arbitration ID.

        :param arbid: a CAN arbitration ID used for BMS communication
        :returns: the message type or ``None`` if error

        """
        # valid range to get a reasonable unit number
        if arbid < 300 or arbid > 454:
            return None
        return int(arbid % 10)

    @staticmethod
    def decode_mv(mvbytes):
        """Return 4-tuple of millivolts from 8 byte input.

        :param mvbytes: a bytes-like of length 8 from BMS reply message
        :returns: 4-tuple with cell voltages as millivolts or ``None`` if error

        This function converts the 8-bytes received from a BMS message and
        converts it to millivolts. Each 8-byte message represents 4 cells so
        4 voltages are returned as a tuple. The units are millivolts (int). If
        the input is not a bytes-like of length 8, then ``None`` is returned.

        """
        if not isinstance(mvbytes, (bytes, bytearray)):
            return None
        if len(mvbytes) != 8:
            return None
        return struct.unpack(">HHHH", mvbytes)

    @staticmethod
    def decode_temp(tempbytes):
        """Return 2-tuple of temperature from 2 byte input.

        :param tempbytes: a bytes-like of length 2 from BMS reply temp message
        :returns: 2-tuple with temperature in C or ``None`` if error

        This function converts the 2-bytes received from a BMS temperature message
        and converts it to temperature in C. Each 2-byte message represents 2
        temperature sensors so 2 temperatures are returned as a tuple. If the
        input is not a bytes-like of length 2, then ``None`` is returned.

        """
        if not isinstance(tempbytes, (bytes, bytearray)):
            return None
        if len(tempbytes) != 2:
            return None
        return (int(tempbytes[0] - 40), int(tempbytes[1] - 40))

    def decode_msg(self, msg):
        """Decode a message meant for this unit.

        :param msg: the message to decode

        This function will decode a message for this unit and will update the
        object data values (voltages and temperatures) with the new decoded
        data.

        If the message is not for this unit, then it is ignored.

        """
        arbid = msg.arbitration_id
        unit = self.unit_from_arbid(msg.arbitration_id)
        if unit != self._unit:
            return
        msgtype = self.type_from_arbid(msg.arbitration_id)

        if msgtype == 0:
            return

        elif msgtype < 4:
            if msg.dlc == 8:
                mv = self.decode_mv(msg.data)
                offset = (msgtype - 1) * 4
                for idx in range(4):
                    self._cellmv[offset + idx] = mv[idx]

        elif msgtype == 4:
            if msg.dlc == 2:
                temps = self.decode_temp(msg.data)
                self._temps[0] = temps[0]
                self._temps[1] = temps[1]

    def probe(self):
        """Determine if unit is present on the CAN bus.

        The CAN bus object must already be set with the `canbus` property.
        This function sends a query message on the bus to this unit and checks
        for an expected response. It returns ``True`` if the unit is present,
        otherwise ``False``.

        """
        self.send_query()
        msgs = self.get_msgs()
        return len(msgs) > 0

    def update(self):
        """Query the unit on the bus and update values.

        Sends a query on the bus for this unit and processes all reply
        messages, decoding and storing the data values for cell voltage
        and temperature sensors.

        """
        self.send_query()
        msgs = self.get_msgs()
        for msg in msgs:
            self.decode_msg(msg)

print("Initializing CAN bus")
bus = can.interface.Bus(bustype="socketcan", channel="can0", bitrate=250000)

units = []
for unit in range(16):
    print(f"Probing unit {unit} ... ", end="")
    bmsunit = bms12(unit=unit, canbus=bus)
    if bmsunit.probe():
        print("Ok")
        units += [bmsunit]
    else:
        print()

for unit in units:
    unit.update()
    print(f"[{unit.unit:2d}] ", end="")
    for mv in unit.cellmv:
        print(f"{mv:5d} ", end="")
    print()

"""
msg = can.Message(arbitration_id=310, is_extended_id=True, data=bytearray([0, 0]))
bus.send(msg)
time.sleep(1)
donext = True
while donext:
    msg = bus.recv(timeout=2)
    if msg:
        print(msg)
        cells = msg.data
        for idx in range(0, msg.dlc, 2):
            mv = cells[idx] * 256 + cells[idx+1]
            print(f"[{int(idx/2)}] {mv}")
    else:
        donext = False
"""
