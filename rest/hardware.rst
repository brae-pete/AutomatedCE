1. Hardware Classes
===============================================

.. toctree::
   :maxdepth: 2
   :caption: Hardware Components:
    installation
.. note::
    New hardware classes should inherit from the base type for its function. A motorized Z-stage should use the Z-stage hardware
    base class, a XY-stage should use the XY-stage base class and so forth.


1.1 Hardware Basics
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Hardware is split into files based off of the intended function. Code to handle applying pressure to the capillary would
be located in the PressureControl.py. In general, if it performs a real world task (apply a pressure, move a stage,
etc...) it will end with the word 'Control'. In addition there are various utility or helper files. These are named
according to their function and should try to be grouped together if possible.

1.2 Image Control
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: ImageControl
    :members:
    :undoc-members:
    :show-inheritance:


1.3 Laser Control
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1.4 Light Control
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
