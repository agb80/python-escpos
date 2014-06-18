#!/usr/bin/python
'''
@author: Manuel F Martinez <manpaz@bashlinux.com>
@organization: Bashlinux
@copyright: Copyright (c) 2012 Bashlinux
@license: GPL
'''

import usb.core
import usb.util
import serial
import socket

from escpos import *
from constants import *
from exceptions import *

class Usb(Escpos):
    """ Define USB printer """

    def __init__(self, idVendor, idProduct, interface=0, in_ep=0x82,
                 out_ep=0x01):
        """
        @param idVendor  : Vendor ID
        @param idProduct : Product ID
        @param interface : USB device interface
        @param in_ep     : Input end point
        @param out_ep    : Output end point
        """
        self.idVendor = idVendor
        self.idProduct = idProduct
        self.interface = interface
        self.handle = None
        self.in_ep = in_ep
        self.out_ep = out_ep
        self.open()


    def open(self):
        """ Search device on USB tree and set is as escpos device """
        self.device = usb.core.find(idVendor=self.idVendor,
                                    idProduct=self.idProduct)
        if self.device is None:
            print "Cable isn't plugged in"

        try:
            # This feature is only available on linux
            if self.device.is_kernel_driver_active(0):
                try:
                    self.device.detach_kernel_driver(0)
                except usb.core.USBError as e:
                    print "Could not detatch kernel driver: %s" % str(e)
        except:
            # Simply pass because windows not implement is_kernel_driver_active
            pass

        try:
            self.device.set_configuration()
        except usb.core.USBError as e:
            print "Could not set configuration: %s" % str(e)


        # get the configuration
        cfg = self.device.get_active_configuration()
        # get the first interface/alternate interface
        interface_number = cfg[(0, 0)].bInterfaceNumber
        alternate_setting = usb.control.get_interface(self.device,
                                                      interface_number)
        intf = usb.util.find_descriptor(
            cfg, bInterfaceNumber=interface_number,
            bAlternateSetting=alternate_setting
        )

        self.handle = usb.util.find_descriptor(
            intf,
            # match the first OUT endpoint
            custom_match=\
            lambda e: \
                usb.util.endpoint_direction(e.bEndpointAddress) == \
                usb.util.ENDPOINT_OUT
        )
        assert self.handle is not None

    def _raw(self, msg):
        """ Print any command sent in raw format """
        self.handle.write(msg)

    def __enter__ (self):
        return self
    
    def __exit__(self, exc, val, trace):
        """ Release USB interface """
        if self.device:
            usb.util.dispose_resources(self.device)
        self.device = None



class Serial(Escpos):
    """ Define Serial printer """

    def __init__(self, devfile="/dev/ttyS0", baudrate=9600,
                 bytesize=8, timeout=1):
        """
        @param devfile  : Device file under dev filesystem
        @param baudrate : Baud rate for serial transmission
        @param bytesize : Serial buffer size
        @param timeout  : Read/Write timeout
        """
        self.devfile = devfile
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.timeout = timeout
        self.open()


    def open(self):
        """ Setup serial port and set is as escpos device """
        self.device = serial.Serial(port=self.devfile,
                                    baudrate=self.baudrate,
                                    bytesize=self.bytesize,
                                    parity=serial.PARITY_NONE,
                                    stopbits=serial.STOPBITS_ONE,
                                    timeout=self.timeout,
                                    dsrdtr=True)

        if self.device is not None:
            print "Serial printer enabled"
        else:
            print "Unable to open serial printer on: %s" % self.devfile


    def _raw(self, msg):
        """ Print any command sent in raw format """
        self.device.write(msg)

    def __enter__ (self):
        return self

    def __exit__(self, exc, val, trace):
        """ Close Serial interface """
        if self.device is not None:
            self.device.close()



class Network(Escpos):
    """ Define Network printer """

    def __init__(self, host, port=9100):
        """
        @param host : Printer's hostname or IP address
        @param port : Port to write to
        """
        self.host = host
        self.port = port
        self.open()


    def open(self):
        """ Open TCP socket and set it as escpos device """
        self.device = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.device.connect((self.host, self.port))

        if self.device is None:
            print "Could not open socket for %s" % self.host


    def _raw(self, msg):
        """ Print any command sent in raw format """
        self.device.send(msg)

    def __enter__ (self):
        return self

    def __exit__(self, exc, val, trace):
        """ Close TCP connection """
        self.device.close()



class File(Escpos):
    """ Define Generic file printer """

    def __init__(self, devfile="/dev/usb/lp0"):
        """
        @param devfile : Device file under dev filesystem
        """
        self.devfile = devfile
        self.open()


    def open(self):
        """ Open system file """
        self.device = open(self.devfile, "wb")

        if self.device is None:
            print "Could not open the specified file %s" % self.devfile


    def _raw(self, msg):
        """ Print any command sent in raw format """
        self.device.write(msg)

    def __enter__ (self):
        return self

    def __exit__(self, exc, val, trace):
        """ Close system file """
        self.device.close()
