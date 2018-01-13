# Python library for ZiGate (zigbee gateway, see : http://zigate.fr)
NB : the homeassistant component is currently under development here : https://github.com/elric91/hass_custom_components

How to use :
- Go in folder
- Launch ipython3 console
```python
from interface import *
z = ZiGate()
conn = ThreadedConnection(z)
z.send_data('0049', 'FFFCFE00')
```
- (last line ask for join request)
- put device in join mode (i.e. long press on button)
- lots of logs
```python
z.list.devices()
```
- will show the list of last info gathered

## Session Example
```
In [5]: zigate.send_data('0049', 'FFFCFE00')
--------------------------------------
REQUEST      :  0049   FFFCFE00
  - standard :  01 00 49 00 05 A3 FF FC FE 02 10 03
  - encoded  :  b'0102104902100215a3fffcfe02121003'
(timestamp :  14:52:18 )
--------------------------------------

In [6]: RESPONSE (@timestamp :  14:52:18 )
  - encoded :  b'01800210021002159202105e021049021003'
  - decoded : 01 80 00 00 05 92 00 5E 00 49 00 03
  - RESPONSE 8000 : Status
    * Sequence:  Success
    * Sequence:  b'5e'
    * Response to command:  b'0049'
RESPONSE (@timestamp :  14:52:28 )
  - encoded :  b'0180480210021ad40210158d02100211d6db5a0210d803'
  - decoded : 01 80 48 00 0A D4 00 15 8D 00 01 D6 DB 5A 00 D8 03
 - RESPONSE : Unknown Message
   * After decoding  :  b'8048000ad400158d0001d6db5a00d8'
   * MsgType         :  b'8048'
   * MsgLength       :  b'000a'
   * RSSI            :  b'd4'
   * ChkSum          :  b'00'
   * Data            :  b'158d0001d6db5a00d8'
RESPONSE (@timestamp :  14:52:30 )
  - encoded :  b'0102104d0210021c6b98240210158d02100211d6db5a80d803'
  - decoded : 01 00 4D 00 0C 6B 98 24 00 15 8D 00 01 D6 DB 5A 80 D8 03
  - This is Device Announce
    * From address:  b'2400'
    * MAC address:  b'158d0001d6db5a80'
    * MAC capability:  b'd8'
    * Full data:  b'2400158d0001d6db5a80d8'
RESPONSE (@timestamp :  14:52:30 )
  - encoded :  b'0102104d0210021c7c98240210158d02100211d6db5a80cf03'
  - decoded : 01 00 4D 00 0C 7C 98 24 00 15 8D 00 01 D6 DB 5A 80 CF 03
  - This is Device Announce
    * From address:  b'2400'
    * MAC address:  b'158d0001d6db5a80'
    * MAC capability:  b'cf'
    * Full data:  b'2400158d0001d6db5a80cf'
RESPONSE (@timestamp :  14:52:30 )
  - encoded :  b'01870211021002134a02100210cf03'
  - decoded : 01 87 01 00 03 4A 00 00 CF 03
 - RESPONSE 8701: Route Discovery Confirmation
   * Sequence:  b'00'
   * Status:  b'00'
   * Network status:  b'cf'
   * Full data:  b'00cf'
RESPONSE (@timestamp :  14:52:31 )
  - encoded :  b'01810212021019e802109824021102100210021002150210420210021c6c75'
  - decoded : 01 81 02 00 19 E8 00 98 24 01 00 00 00 05 00 42 00 0C 6C 75 6D 693
  - RESPONSE 8102 : Attribute Report
    * Sensor type announce (Start after pairing 1)
   * type :  b'lumi.weather'
  - From address:  b'9824'
  - Source Ep:  b'01'
  - Cluster ID:  b'0000'
  - Attribute ID:  b'0005'
  - Attribute size:  b'000c'
  - Attribute type:  b'42'
  - Attribute data:  b'6c756d692e77656174686572'
  - Full data:  b'982401000000050042000c6c756d692e77656174686572cf'
RESPONSE (@timestamp :  14:52:31 )
  - encoded :  b'018102120210021edc02109824021102100210021002110210200210021102'
  - decoded : 01 81 02 00 0E DC 00 98 24 01 00 00 00 01 00 20 00 01 03 CF 03
  - RESPONSE 8102 : Attribute Report
    * Sensor type announce (Start after pairing 1)
  - From address:  b'9824'
  - Source Ep:  b'01'
  - Cluster ID:  b'0000'
  - Attribute ID:  b'0001'
  - Attribute size:  b'0001'
  - Attribute type:  b'20'
  - Attribute data:  b'03'
  - Full data:  b'982401000000010020000103cf'
RESPONSE (@timestamp :  14:52:31 )
  - encoded :  b'01810212021032021c02119824021102100210ff0211021042021025021121'
  - decoded : 01 81 02 00 32 0C 01 98 24 01 00 00 FF 01 00 42 00 25 01 21 A9 0B3
  - RESPONSE 8102 : Attribute Report
    * Something announce (Start after pairing 2)
  - From address:  b'9824'
  - Source Ep:  b'01'
  - Cluster ID:  b'0000'
  - Attribute ID:  b'ff01'
  - Attribute size:  b'0025'
  - Attribute type:  b'42'
  - Attribute data:  b'0121a90b0421a8010521090006240100000000642911086521b01966'
  - Full data:  b'9824010000ff01004200250121a90b0421a80105210900062401000000006'
RESPONSE (@timestamp :  14:52:35 )
  - encoded :  b'018102120210021fc602129824021102140212021002100210290210021202'
  - decoded : 01 81 02 00 0F C6 02 98 24 01 04 02 00 00 00 29 00 02 08 1F CF 03
  - RESPONSE 8102 : Attribute Report
    * Measurement: Temperature
    * Value:  20.79 °C
  - From address:  b'9824'
  - Source Ep:  b'01'
  - Cluster ID:  b'0402'
  - Attribute ID:  b'0000'
  - Attribute size:  b'0002'
  - Attribute type:  b'29'
  - Attribute data:  b'081f'
  - Full data:  b'9824010402000000290002081fcf'
RESPONSE (@timestamp :  14:52:35 )
  - encoded :  b'018102120210021fbe02139824021102140215021002100210210210021218'
  - decoded : 01 81 02 00 0F BE 03 98 24 01 04 05 00 00 00 21 00 02 18 79 CF 03
  - RESPONSE 8102 : Attribute Report
    * Measurement: Humidity
    * Value:  62.65 %
  - From address:  b'9824'
  - Source Ep:  b'01'
  - Cluster ID:  b'0405'
  - Attribute ID:  b'0000'
  - Attribute size:  b'0002'
  - Attribute type:  b'21'
  - Attribute data:  b'1879'
  - Full data:  b'98240104050000002100021879cf'
RESPONSE (@timestamp :  14:52:35 )
  - encoded :  b'018102120210021f021b021498240211021402130210021002102902100212'
  - decoded : 01 81 02 00 0F 0B 04 98 24 01 04 03 00 00 00 29 00 02 03 DE CF 03
  - RESPONSE 8102 : Attribute Report
    * Atmospheric pressure
    * Value:  990 mb
  - From address:  b'9824'
  - Source Ep:  b'01'
  - Cluster ID:  b'0403'
  - Attribute ID:  b'0000'
  - Attribute size:  b'0002'
  - Attribute type:  b'29'
  - Attribute data:  b'03de'
  - Full data:  b'982401040300000029000203decf'
RESPONSE (@timestamp :  14:52:35 )
  - encoded :  b'018102120210021e3e0214982402110214021302101402102802100211ffcf'
  - decoded : 01 81 02 00 0E 3E 04 98 24 01 04 03 00 14 00 28 00 01 FF CF 03
  - RESPONSE 8102 : Attribute Report
    * Atmospheric pressure
    * Value unknown
  - From address:  b'9824'
  - Source Ep:  b'01'
  - Cluster ID:  b'0403'
  - Attribute ID:  b'0014'
  - Attribute size:  b'0001'
  - Attribute type:  b'28'
  - Attribute data:  b'ff'
  - Full data:  b'9824010403001400280001ffcf'
RESPONSE (@timestamp :  14:52:35 )
  - encoded :  b'018102120210021f54021498240211021402130210100210290210021226b4'
  - decoded : 01 81 02 00 0F 54 04 98 24 01 04 03 00 10 00 29 00 02 26 B4 CF 03
  - RESPONSE 8102 : Attribute Report
    * Atmospheric pressure
    * Value:  990.8 mb
  - From address:  b'9824'
  - Source Ep:  b'01'
  - Cluster ID:  b'0403'
  - Attribute ID:  b'0010'
  - Attribute size:  b'0002'
  - Attribute type:  b'29'
  - Attribute data:  b'26b4'
  - Full data:  b'982401040300100029000226b4cf'
RESPONSE (@timestamp :  14:52:38 )
  - encoded :  b'018102120210021fcc02159824021102140212021002100210290210021202'
  - decoded : 01 81 02 00 0F CC 05 98 24 01 04 02 00 00 00 29 00 02 08 12 CF 03
  - RESPONSE 8102 : Attribute Report
    * Measurement: Temperature
    * Value:  20.66 °C
  - From address:  b'9824'
  - Source Ep:  b'01'
  - Cluster ID:  b'0402'
  - Attribute ID:  b'0000'
  - Attribute size:  b'0002'
  - Attribute type:  b'29'
  - Attribute data:  b'0812'
  - Full data:  b'98240104020000002900020812cf'
RESPONSE (@timestamp :  14:52:38 )
  - encoded :  b'018102120210021f5702169824021102140215021002100210210210021217'
  - decoded : 01 81 02 00 0F 57 06 98 24 01 04 05 00 00 00 21 00 02 17 9A CF 03
  - RESPONSE 8102 : Attribute Report
    * Measurement: Humidity
    * Value:  60.42 %
  - From address:  b'9824'
  - Source Ep:  b'01'
  - Cluster ID:  b'0405'
  - Attribute ID:  b'0000'
  - Attribute size:  b'0002'
  - Attribute type:  b'21'
  - Attribute data:  b'179a'
  - Full data:  b'9824010405000000210002179acf'
RESPONSE (@timestamp :  14:52:38 )
  - encoded :  b'018102120210021f1502179824021102140213021002100210290210021202'
  - decoded : 01 81 02 00 0F 15 07 98 24 01 04 03 00 00 00 29 00 02 03 DE D2 03
  - RESPONSE 8102 : Attribute Report
    * Atmospheric pressure
    * Value:  990 mb
  - From address:  b'9824'
  - Source Ep:  b'01'
  - Cluster ID:  b'0403'
  - Attribute ID:  b'0000'
  - Attribute size:  b'0002'
  - Attribute type:  b'29'
  - Attribute data:  b'03de'
  - Full data:  b'982401040300000029000203ded2'
RESPONSE (@timestamp :  14:52:38 )
  - encoded :  b'018102120210021e200217982402110214021302101402102802100211ffd2'
  - decoded : 01 81 02 00 0E 20 07 98 24 01 04 03 00 14 00 28 00 01 FF D2 03
  - RESPONSE 8102 : Attribute Report
    * Atmospheric pressure
    * Value unknown
  - From address:  b'9824'
  - Source Ep:  b'01'
  - Cluster ID:  b'0403'
  - Attribute ID:  b'0014'
  - Attribute size:  b'0001'
  - Attribute type:  b'28'
  - Attribute data:  b'ff'
  - Full data:  b'9824010403001400280001ffd2'
RESPONSE (@timestamp :  14:52:38 )
  - encoded :  b'018102120210021f4a021798240211021402130210100210290210021226b4'
  - decoded : 01 81 02 00 0F 4A 07 98 24 01 04 03 00 10 00 29 00 02 26 B4 D2 03
  - RESPONSE 8102 : Attribute Report
    * Atmospheric pressure
    * Value:  990.8 mb
  - From address:  b'9824'
  - Source Ep:  b'01'
  - Cluster ID:  b'0403'
  - Attribute ID:  b'0010'
  - Attribute size:  b'0002'
  - Attribute type:  b'29'
  - Attribute data:  b'26b4'
  - Full data:  b'982401040300100029000226b4d2'
RESPONSE (@timestamp :  14:52:42 )
  - encoded :  b'018102120210021ffa02189824021102140212021002100210290210021202'
  - decoded : 01 81 02 00 0F FA 08 98 24 01 04 02 00 00 00 29 00 02 08 29 CF 03
  - RESPONSE 8102 : Attribute Report
    * Measurement: Temperature
    * Value:  20.89 °C
  - From address:  b'9824'
  - Source Ep:  b'01'
  - Cluster ID:  b'0402'
  - Attribute ID:  b'0000'
  - Attribute size:  b'0002'
  - Attribute type:  b'29'
  - Attribute data:  b'0829'
  - Full data:  b'98240104020000002900020829cf'
RESPONSE (@timestamp :  14:52:42 )
  - encoded :  b'018102120210021f3902199824021102140215021002100210210210021216'
  - decoded : 01 81 02 00 0F 39 09 98 24 01 04 05 00 00 00 21 00 02 16 FA CF 03
  - RESPONSE 8102 : Attribute Report
    * Measurement: Humidity
    * Value:  58.82 %
  - From address:  b'9824'
  - Source Ep:  b'01'
  - Cluster ID:  b'0405'
  - Attribute ID:  b'0000'
  - Attribute size:  b'0002'
  - Attribute type:  b'21'
  - Attribute data:  b'16fa'
  - Full data:  b'982401040500000021000216facf'
RESPONSE (@timestamp :  14:52:42 )
  - encoded :  b'018102120210021f0215021a98240211021402130210021002102902100212'
  - decoded : 01 81 02 00 0F 05 0A 98 24 01 04 03 00 00 00 29 00 02 03 DE CF 03
  - RESPONSE 8102 : Attribute Report
    * Atmospheric pressure
    * Value:  990 mb
  - From address:  b'9824'
  - Source Ep:  b'01'
  - Cluster ID:  b'0403'
  - Attribute ID:  b'0000'
  - Attribute size:  b'0002'
  - Attribute type:  b'29'
  - Attribute data:  b'03de'
  - Full data:  b'982401040300000029000203decf'
RESPONSE (@timestamp :  14:52:42 )
  - encoded :  b'018102120210021e30021a982402110214021302101402102802100211ffcf'
  - decoded : 01 81 02 00 0E 30 0A 98 24 01 04 03 00 14 00 28 00 01 FF CF 03
  - RESPONSE 8102 : Attribute Report
    * Atmospheric pressure
    * Value unknown
  - From address:  b'9824'
  - Source Ep:  b'01'
  - Cluster ID:  b'0403'
  - Attribute ID:  b'0014'
  - Attribute size:  b'0001'
  - Attribute type:  b'28'
  - Attribute data:  b'ff'
  - Full data:  b'9824010403001400280001ffcf'
RESPONSE (@timestamp :  14:52:42 )
  - encoded :  b'018102120210021f5a021a98240211021402130210100210290210021226b4'
  - decoded : 01 81 02 00 0F 5A 0A 98 24 01 04 03 00 10 00 29 00 02 26 B4 CF 03
  - RESPONSE 8102 : Attribute Report
    * Atmospheric pressure
    * Value:  990.8 mb
  - From address:  b'9824'
  - Source Ep:  b'01'
  - Cluster ID:  b'0403'
  - Attribute ID:  b'0010'
  - Attribute size:  b'0002'
  - Attribute type:  b'29'
  - Attribute data:  b'26b4'
  - Full data:  b'982401040300100029000226b4cf
 

In [6]: zigate.list_devices()
-- DEVICE REPORT -------------------------
- addr :  b'2400'
    *  MAC  :  b'158d0001d6db5a80'
- addr :  b'9824'
    *  (b'0000', b'0005')  :  b'6c756d692e77656174686572'  ( General: Basic )
    *  Last seen  :  2017-12-30 14:52:42
    *  Type  :  b'lumi.weather'
    *  (b'0000', b'0001')  :  b'03'  ( General: Basic )
    *  (b'0000', b'ff01')  :  b'0121a90b0421a8010521090006240100000000642911086521b019662b178301000a210000'  ( General: Basic )
    *  (b'0402', b'0000')  :  b'0829'  ( Measurement: Temperature )
    *  Temperature  :  20.89
    *  (b'0405', b'0000')  :  b'16fa'  ( Measurement: Humidity )
    *  Humidity  :  58.82
    *  (b'0403', b'0000')  :  b'03de'  ( Measurement: Atmospheric Pressure )
    *  Pressure  :  990
    *  (b'0403', b'0014')  :  b'ff'  ( Measurement: Atmospheric Pressure )
    *  (b'0403', b'0010')  :  b'26b4'  ( Measurement: Atmospheric Pressure )
    *  Pressure - detailed  :  990.8
-- DEVICE REPORT - END -------------------
```
