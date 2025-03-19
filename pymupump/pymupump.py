
#     pymupump - Python interface to Harvard Apparatus Microliter OEM Syringe Pump
#     Copyright (C) 2024  Raphael Kriegl

#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.

#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.

#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <https://www.gnu.org/licenses/>.

import threading 
import serial
import argparse
import logging
from time import sleep

def format_float_str(string):
    """Return string without useless information.

     Return string with trailing zeros after a decimal place, trailing
     decimal points, and leading and trailing spaces removed.
     """
    if "." in string:
        string = string.rstrip('0')

    string = string.lstrip('0 ')
    string = string.rstrip(' .')

    return string

class Chain(serial.Serial):
    """Create Chain object.

    Harvard syringe pumps are daisy chained together in a 'pump chain'
    off a single serial port. A pump address is set on each pump. You
    must first create a chain to which you then add Pump objects.

    Chain is a subclass of serial.Serial. Chain creates a serial.Serial
    instance with the required parameters, flushes input and output
    buffers (found during testing that this fixes a lot of problems) and
    logs creation of the Chain.
    """
    def __init__(self, port):
        super().__init__(port=port, stopbits=serial.STOPBITS_TWO, parity=serial.PARITY_NONE, timeout=2)
        self.flushOutput()
        self.flushInput()
        logging.info(f'Chain created on {port}')
    


class Microliter:
    """Class to contol Harvard Apparatus Microliter OEM Pump as an extension to pumpy.

    :param chain: chain object to attatch to
    :param address: optional pump address. Default is 0.
    :param name: optional name for the pump to be used in logging. Default is Pump 11.
    """

    def __init__(self, chain, address=0, name='Microliter'):
        self.name = name
        self.serialcon: serial.Serial = chain
        self.address = f'{address:02.0f}'
        self.diameter = None
        self.flowrate = None
        self.targetvolume = None
        self._running = False
        self._timeout = 20
        self._mutex = threading.Lock()

        """Query model and version number of firmware to check pump is
        OK. Responds with a load of stuff, but the last three characters
        are XXY, where XX is the address and Y is pump status. :, > or <
        when stopped, running forwards, or running backwards. Confirm
        that the address is correct. This acts as a check to see that
        the pump is connected and working."""
        try:
            self.write('VER')
            resp = self.read(17)

            if int(resp[-3:-1]) != int(self.address):
                raise PumpError(f'No response from pump at address {self.address}')
        except PumpError:
            self.serialcon.close()
            raise

        logging.info(f'{self.name}: created at address {self.address} on {self.serialcon.port}' )

    def __repr__(self):
        string = ''
        for attr in self.__dict__:
            string += f'{attr}: {self.__dict__[attr]}\n' 
        return string


    def write(self,command):
        """ write command to pump

        :param command: command as string 
        """
        self.serialcon.write(str(self.address + command + '\r').encode())

    def read(self,bytes=5):
        """ read number of bytes from serial buffer

        :param bytes: number of bytes to read
        :returns: bytes read from buffer
        """
        response = self.serialcon.read(bytes).decode().strip()

        if len(response) == 0:
            raise PumpError(f'{self.name}: no response to command')
        else:
            return response
        
    def readall(self, wait=True):
        """ read complete serial buffer

        :param wait: wait for response. Default is True
        :returns: bytes read from buffer
        """
        cntr = 0
        sleep(0.1)
        response = self.serialcon.read_all().decode().strip()
        while len(response) == 0 and wait and cntr < self._timeout:
            sleep(0.1)
            cntr += 1
            response = self.serialcon.read_all().decode().strip()

        if len(response) == 0 and wait:
            raise PumpError(f'{self.name}: no response to command')
        else:
            return response

    def query(self, command, ans_len=-1, wait_ans=True):
        """ write command to pump and read response
        
        :param command: command as string
        :param ans_len: number of bytes to read from buffer. Default is -1, which reads all bytes
        :param wait_ans: wait for response. Default is True
        """
        # mutex to prevent multiple threads from writing to the pump at the same time
        self._mutex.acquire(True)
        self.write(command)

        if ans_len == -1:
            response = self.readall(wait=wait_ans)
        else:
            response = self.read(bytes=ans_len)
        self._mutex.release()
        return response



    def setdiameter(self, diameter):
        """Set syringe diameter

        :param diameter: the diameter fo the syringe in mm

        .. note:: 
            syringe diameter range is 0.1-4.61 mm. 
            Note that the pump ignores precision greater than 2 decimal places. 
            If more d.p. are specificed the diameter will be truncated.
        """
        diameter = round(diameter,3)
        if diameter > 4.61 or diameter < 0.1:
            raise PumpError(f'{self.name}: diameter {diameter} mm is out of range')
        
        diam_str = format_float_str(str(diameter))

        # Send command   
        #self.write('MMD ' + diam_str)
        resp = self.query('MMD ' + diam_str)

        # Pump replies with address and status (:, < or >)        
        if (resp[-1] in ":<>*IWDT" or "*" in resp):
            # check if diameter has been set correctlry
            # self.write('DIA')
            # resp = self.read(15)
            resp = self.query('DIA', ans_len=15)
            returned_diameter = format_float_str(resp[0:9])
            
            # Check diameter was set accurately
            if float(returned_diameter) != diameter:
                logging.error(f'{self.name}: set diameter ({diam_str} mm) does not match diameter'
                              f' returned by pump ({returned_diameter} mm)')
            else:
                self.diameter = float(returned_diameter)
                logging.info(f'{self.name}: diameter set to {self.diameter} mm')
        else:
            raise PumpError(f'{self.name}: unknown response to setdiameter: {resp}')

    def setflowrate(self, flowrate):
        """Set flow rate

        :param flowrate: flowrate in ul/min

        .. note:: 
            The pump will tell you if the specified flow rate is out of range.
            This depends on the syringe diameter.

        """
        flowrate = format_float_str(str(flowrate))

        # self.write('ULM ' + flowrate)
        # resp = self.readall()
        # self.write('ULMW ' + flowrate)
        # resp = self.readall()

        resp = self.query('ULM ' + flowrate)
        resp = self.query('ULMW ' + flowrate)
        
        if (resp[-1] in ":<>*IWDT" or "*" in resp):
            # Flow rate was sent, check it was set correctly
            # self.write('RAT')
            # resp = self.readall()
            resp = self.query('RAT')
            returned_flowrate = resp.split(' ')[0]

            if float(returned_flowrate) != float(flowrate):
                logging.error(f'{self.name}: set infuse flowrate ({flowrate} uL/min) does not match'
                              f'flowrate returned by pump ({returned_flowrate} uL/min)')
            else:
                self.flowrate = returned_flowrate
                logging.info(f'{self.name}: infuse flow rate set to {self.flowrate} uL/min')
            # self.write('RATW')
            # resp = self.readall()
            resp = self.query('RATW')
            returned_flowrate = resp.split(' ')[0]

            if float(returned_flowrate) != float(flowrate):
                logging.error(f'{self.name}: set withdraw flowrate ({flowrate} uL/min) does not match'
                              f'flowrate returned by pump ({returned_flowrate} uL/min)')

            else:
                self.flowrate = returned_flowrate
                logging.info(f'{self.name}: withdraw flow rate set to {self.flowrate} uL/min')
        elif 'OOR' in resp:
            raise PumpError(f'{self.name}: flow rate ({flowrate} uL/min) is out of range')
        else:
            raise PumpError(f'{self.name}: unknown response: {resp}')
            
    def infuse(self):
        """Start infusing pump."""
        # self.write('RUN')
        # resp = self.readall()      
        resp = self.query('RUN')
        if not '>' in resp:
            raise PumpError(f"{self.name}: Pump did not start infuse!: {resp}")  
        logging.info(f'{self.name}: infusing')

    def withdraw(self):
        """Start withdrawing pump."""
        # self.write('RUNW')
        # resp = self.readall()
        resp = self.query('RUNW')
        if not '<' in resp:
            raise PumpError(f"{self.name}: Pump did not start withdraw!: {resp}")
        logging.info(f'{self.name}: withdrawing')

    def stop(self):
        """ stop pump movement """
        logging.info(f"{self.name}: stopping pump")
        
        # self.write("STP")
        # resp = self.readall(wait=False)
        resp = self.query('STP', wait_ans=False)
        if not resp[-1] in ":*IWDT":
            raise PumpError(f"{self.name}: Pump did not stop: {resp}")

    def settargetvolume(self, targetvolume):
        """Set the target volume to infuse or withdraw (microlitres)."""
        # clear infuse/withdraw target
        resp = self.query('CLT')
        resp = self.query('CLTW')
        resp = self.query('CLV')
        resp = self.query('CLVW')
        # set new infuse/withdraw target
        resp = self.query('ULT ' + str(targetvolume))
        resp = self.query('ULTW ' + str(targetvolume))

        # response should be CRLFXX:, CRLFXX>, CRLFXX< where XX is address

        if resp[-1] in ":<>*IWDT" or "*" in resp:
            self.targetvolume = float(targetvolume)
            logging.info(f'{self.name}: target volume set to {self.targetvolume} uL')
        else:
            raise PumpError(f'{self.name}: unknown response: {resp}')

    def waituntiltarget(self):
        """Wait until the pump has reached its target volume."""
        logging.info(f'{self.name}: waiting until target reached')
        self._running = True

        try:
            resp = self.query('VOL')
        except UnicodeDecodeError:
            pass

        if not '<' in resp and not '>' in resp:
            raise PumpError(f'{self.name}: not infusing/withdrawing - infuse or '
                            'withdraw first')

        while self._running:
            try:
                resp = self.query('VOL')
                if not '<' in resp and not '>' in resp:
                # pump has come to a halt
                    break

            except UnicodeDecodeError:
                pass
            sleep(0.1)
        
        logging.info(f'{self.name}: stopped')


class PumpError(Exception):
    pass

# Command line options
# Run with -h flag to see help
def main():
# if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Command line interface to '
                                     'control Harvard Apparatus'
                                     'Microliter OEM Syringe Pump.')
    parser.add_argument('port', help='serial port')
    parser.add_argument('address', help='pump address',type=int,
                         nargs='?', default=0)
    parser.add_argument('-d', dest='diameter', help='set syringe diameter',
                        type=int)
    parser.add_argument('-f', dest='flowrate', help='set flow rate')
    parser.add_argument('-t', dest='targetvolume', help='set target volume')
    parser.add_argument('-w', dest='wait', help='wait for target volume to be'
                        ' reached; use with -infuse or -withdraw',
                        action='store_true')
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-infuse', action='store_true')
    group.add_argument('-withdraw', action="store_true")
    group.add_argument('-stop', action="store_true")

    args = parser.parse_args()

    # Command precedence:
    # 1. stop
    # 2. set diameter
    # 3. set flow rate
    # 4. set target
    # 5. infuse|withdraw (+ wait for target volume)

    try:
        chain = Chain(args.port)
        pump = Microliter(chain,args.address, name='11')

        if args.stop:
            pump.stop()

        if args.diameter:
            pump.setdiameter(args.diameter)

        if args.flowrate:
            pump.setflowrate(args.flowrate)

        if args.targetvolume:
            pump.settargetvolume(args.targetvolume)

        if args.infuse:
            pump.infuse()
            if args.wait:
                pump.waituntiltarget()

        if args.withdraw:
            pump.withdraw()
            if args.wait:
                pump.waituntiltarget()
    finally:
        chain.close()
