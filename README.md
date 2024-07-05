# pymupump
Python interface for controlling Harvard Apparatus Microliter OEM Syringe Pump

Derived from now inactive library [pumpy](https://github.com/tomwphillips/pumpy), thanks to tomwphillips.

## Installation

`pip install pymupump`


## Usage

```py
import pymupump as pmp

chain = pmp.Chain('COM1') # your port
pump = pmp.Microliter(chain) 
# if using multiple pumps on the same port
# you might want to specify another adress and name
pump2 = pmp.Microliter(chain, 1, "Pump2")

pump.setdiameter(2) # diameter of syringe in mm, range is 0.1 - 4.61
pump.setflowrate(3) # set flowrte in ul/min

pump.settargetvolume(2) # set infuse or withdraw target volume in ul

pump.infuse()
# or
pump.withdraw()

pump.waituntiltarget() # block until pump finishes

pump.stop() # stop pump

```