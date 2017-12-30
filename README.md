# Python draft implementation for ZiGate
ZiGate / ZigBee devices test program

How to use :
- Go in folder
- Launch ipython3 console
```python
from interface import *
zigate = ZiGate()
zigate.send_data('0049', 'FFFCFE0210')
```
- (last line ask for join request)
- put device in join mode (i.e. long press on button)
- lots of logs
```python
list.devices()
```
- will show the list of last info gathered

NB : the homeassistant component is currently under development here : https://github.com/elric91/hass_custom_components
