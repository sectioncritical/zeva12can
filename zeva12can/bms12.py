import struct
import time
import can

class BMS12(object):
    """Zeva BMS12 Communications Library.

    This class provides an abstraction of the Zeva BMS-12 CAN protocol. An
    instance of the class represents one Zeva BMS-12 unit on the bus.

    This class provides many methods, but only a few are needed to get updates
    from the BMS hardware. Here is a typical example:

    ::

        # initialize a CAN bus
        bus = can.interface.Bus(...)

        # create a bms12 unit
        unit1 = BMS12(1, shuntmv=3800, canbus=bus)

        # check if unit is present
        if not unit1.probe():
            # process error

        # update the voltage readings
        unit1.update()

        # read a cell voltage (in millivolts)
        cell1 = unit1.cellmv[1]

        # change the shunt voltage
        unit1.shuntmv = 3700 # change to 3.7 V

        # need to run update in order for new value to take effect
        unit1.update()  # will also update voltage readings

    """

    def __init__(self, unit: int, shuntmv: int=0, canbus=None):
        """Create a new bms12 instance.

        :param unit: the unit number (0-15)
        :param shuntmv: the initial shunt voltage in millivolts
        :param canbus: a :meth:`can.interface.Bus` object from the ``can`` module

        If ``shuntmv`` is 0 or not specied, then shunting is disabled. The
        shunt level can be changed at any time using the property
        :meth:`shuntmv`.

        The ``canbus`` does not need to be specified to create the object, but
        it must be set using the property :meth:`canbus` before any operations
        can be performed.

        """
        self._unit = unit
        self._shuntlvl = shuntmv
        self._bus = canbus
        self._cellmv = [0] * 12
        self._temps = [0, 0]
        self._ver = [0, 0, 0]

    @property
    def unit(self) -> int:
        """Get the unit number."""
        return self._unit

    @property
    def shuntmv(self) -> int:
        """Get the current shunt level, in millivolts."""
        return self._shuntlvl

    @shuntmv.setter
    def shuntmv(self, mv: int):
        """Set a new shunt level, in millivolts.

        You need to update the BMS unit by using :meth:`send_query()` before
        the new setting will take effect.

        """
        self._shuntlvl = mv

    @property
    def canbus(self):
        """Get the current CAN bus object."""
        return self._bus

    @canbus.setter
    def canbus(self, bus):
        """Set a new CAN bus object to use for communication."""
        self._bus = bus

    @property
    def cellmv(self):
        """Get the list of 12 cell voltages, in millivolts.

        You can add an index to get the value for a specific cell. For example
        ``bmsunit.cellmv[2]``, to get the third cell value. Valid indexes are
        0-11.

        """
        return self._cellmv

    @property
    def temperature(self):
        """Get the list of two temperatures, in C."""
        return self._temps

    @property
    def version(self):
        """Get the firmware version."""
        return self._ver

    def send_query(self):
        """Send query packet with shunt level to unit.

        Sends the query message to the unit. This also sets the shunt level.
        The shunt level should already be set using the `shuntmv` property.

        """
        arbid = 300 + (self._unit * 10)
        payload = struct.pack(">H", self._shuntlvl)
        msg = can.Message(arbitration_id=arbid, is_extended_id=True, data=payload)
        self._bus.send(msg)

    def send_version_cmd(self):
        """Send command to request firmware version."""
        arbid = 300 + (self._unit * 10) + 5
        payload = struct.pack("BBBBBBBB", 1, 0, 0, 0, 0, 0, 0, 0)
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

        elif msgtype == 6:
            if msg.data[0] == 1:
                self._ver[0] = msg.data[1]
                self._ver[1] = msg.data[2]
                self._ver[2] = msg.data[3]

    def probe(self):
        """Determine if unit is present on the CAN bus.

        The CAN bus object must already be set with the `canbus` property.
        This function sends a version request command and checks for an
        expected response. If there is a response it is decoded into firmware
        version and the value returned. Otherwise the function returns
        ``None``.

        """
        self.send_version_cmd()
        msgs = self.get_msgs()
        if len(msgs) > 0:
            self.decode_msg(msgs[0])
            return self.version
        return None

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
