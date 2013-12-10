Changelog
=========
DecoTengu 0.4.0
---------------
- trimix support implemented
- travel gas mixes can be added to gas mix list
- added Buhlmann equation description to the documentation

DecoTengu 0.3.0
---------------
- all calculations are performed using pressure instead of depth
- implemented deco model validator to check if first decompression stop is
  at ascent ceiling

DecoTengu 0.2.0
---------------
- gas mix switch is performed in more controlled manner
- API has changed as conveyor functionality is removed from decompression
  engine class; instead, conveyor objects can be used to expand dive
  profile dive steps by replacing Engine.calculate method
- added more detailed Schreiner equation description

DecoTengu 0.1.0
---------------
- initial release

.. vim: sw=4:et:ai
