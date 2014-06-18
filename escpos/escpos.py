#!/usr/bin/python
'''
@author: Manuel F Martinez <manpaz@bashlinux.com>
@organization: Bashlinux
@copyright: Copyright (c) 2012 Bashlinux
@license: GPL
'''

from PIL import Image
import qrcode
import time

from constants import *
from exceptions import *

class Escpos:
    """ ESC/POS Printer object """
    device = None


    def _printImgMatrix(self, imgMatrix, width, height, res, align):
        """Print an image as a pixel access object with binary colour."""
        if res == "high":
            scaling = 24
            currentpxWidth = self.pxWidth * 2
        else:
            scaling = 8
            currentpxWidth = self.pxWidth
        if width > currentpxWidth:
            raise ValueError("Image too wide. Maximum width is configured to be " + str(currentpxWidth) + "pixels. The image is " + str(width) + " pixels wide.")
        tmp = ''
        for yScale in range(-(-height / scaling)):
            # Set mode to hex and 8-dot single density (60 dpi).
            if res == "high":
                outList = ["0x1B", "0x2A", "0x21"]
            else:
                outList = ["0x1B", "0x2A", "0x00"]
            # Add width to the communication to the printer.
            # Depending on the alignment we count that in and add blank
            # vertical lines to the outList
            if align == "left":
                blanks = 0
            if align == "center":
                blanks = (currentpxWidth - width) / 2
            if align == "right":
                blanks = currentpxWidth - width
            highByte = (width + blanks) / 256
            lowByte = (width + blanks) % 256
            outList.append(hex(lowByte))
            outList.append(hex(highByte))
            if res == "high":
                blanks *= 3
            if align == "left":
                pass
            if align == "center":
                for i in range(blanks):
                    outList.append(hex(0))
            if align == "right":
                for i in range(blanks):
                    outList.append(hex(0))
            for x in range(width):
                """Compute hex string for one vertical bar of 8 dots
                (zero padded from the bottom if necessary).
                """
                binStr = ""
                for y in range(scaling):
                    """ Indirect zero padding.
                    Do not try to extract values from images beyond its size.
                    """
                    if (yScale * scaling + y) < height:
                        binStr += "0" if imgMatrix[x, yScale * scaling + y] == 255 else "1"
                    # Zero padding
                    else:
                        binStr += "0"
                outList.append(hex(int(binStr[0:8], 2)))
                if res == "high":
                    outList.append(hex(int(binStr[8:16], 2)))
                    outList.append(hex(int(binStr[16:24], 2)))
            for element in outList:
                try:
                    tmp += chr(int(element, 16))
                except:
                    raise

        self.text(tmp)


    def _printImgFromPILObj(self, img, res="high", align="center", scale=None):
        """The object must be a Python ImageLibrary object,
        and the colordepth should be set to 1."""
        try:
            # If a scaling factor has been indicated
            if scale:
                assert type(scale) == float
                if scale > 1.0 or scale <= 0.0:
                    raise ValueError("Scaling factor must be > 0.0 and <= 1.0")
                # Give a consistent output regardless of the resolution setting
                scale *= self.printer.pxWidth / float(img.size[0])
                if res is "high":
                    scaleTuple = (scale * 2, scale * 2)
                else:
                    scaleTuple = (scale, scale * 2 / 3.0)
                # Convert to binary colour depth and resize
                imgB = img.resize([int(scaleTuple[i] * img.size[i]) for i in range(2) ]).convert("1")
            else:
                # Convert to binary colour depth
                imgB = img.convert("1")
            # Convert to a pixel access object
            imgMatrix = imgB.load()
            width = imgB.size[0]
            height = imgB.size[1]
            # Print it
            self._printImgMatrix(imgMatrix, width, height, res, align)
        except:
            raise


    def image(self, fname, res="high", align="center", scale=None):
        """Print an image from a file.
        resolution may be set to "high" or "low". Setting it to low makes
        the image a bit narrow (90x60dpi instead of 180x180 dpi) unless scale
        is also set. Align may be set to "left", "center" or "right".
        scale resizes the image with that factor, where 1.0 is the full
        width of the paper."""
        try:
            from PIL import Image
            # Open file and convert to black/white (colour depth of 1 bit)
            img = Image.open(fname).convert("1")
            self._printImgFromPILObj(img, res, align, scale)
        except:
            raise


    def qr(self, text):
        """ Print QR Code for the provided string """
        qr_code = qrcode.QRCode(version=4, box_size=4, border=1)
        qr_code.add_data(text)
        qr_code.make(fit=True)
        qr_img = qr_code.make_image()
        im = qr_img._img.convert("RGB")
        # Convert the RGB image in printable image
        self._convert_image(im)


    def barcode(self, code, bc, width, height, pos, font):
        """ Print Barcode """
        # Align Bar Code()
        self._raw(TXT_ALIGN_CT)
        # Height
        if height >= 2 or height <= 6:
            self._raw(BARCODE_HEIGHT)
        else:
            raise BarcodeSizeError()
        # Width
        if width >= 1 or width <= 255:
            self._raw(BARCODE_WIDTH)
        else:
            raise BarcodeSizeError()
        # Font
        if font.upper() == "B":
            self._raw(BARCODE_FONT_B)
        else:  # DEFAULT FONT: A
            self._raw(BARCODE_FONT_A)
        # Position
        if pos.upper() == "OFF":
            self._raw(BARCODE_TXT_OFF)
        elif pos.upper() == "BOTH":
            self._raw(BARCODE_TXT_BTH)
        elif pos.upper() == "ABOVE":
            self._raw(BARCODE_TXT_ABV)
        else:  # DEFAULT POSITION: BELOW
            self._raw(BARCODE_TXT_BLW)
        # Type
        if bc.upper() == "UPC-A":
            self._raw(BARCODE_UPC_A)
        elif bc.upper() == "UPC-E":
            self._raw(BARCODE_UPC_E)
        elif bc.upper() == "EAN13":
            self._raw(BARCODE_EAN13)
        elif bc.upper() == "EAN8":
            self._raw(BARCODE_EAN8)
        elif bc.upper() == "CODE39":
            self._raw(BARCODE_CODE39)
        elif bc.upper() == "ITF":
            self._raw(BARCODE_ITF)
        elif bc.upper() == "NW7":
            self._raw(BARCODE_NW7)
        else:
            raise BarcodeTypeError()
        # Print Code
        if code:
            self._raw(code)
        else:
            raise exception.BarcodeCodeError()


    def text(self, txt):
        """ Print alpha-numeric text """
        if txt:
            self._raw(txt)
        else:
            raise TextError()


    def set(self, align='left', font='a', type='normal', width=1, height=1):
        """ Set text properties """
        # Width
        if width == 2 and height != 2:
            self._raw(TXT_NORMAL)
            self._raw(TXT_2WIDTH)
        elif height == 2 and width != 2:
            self._raw(TXT_NORMAL)
            self._raw(TXT_2HEIGHT)
        elif height == 2 and width == 2:
            self._raw(TXT_2WIDTH)
            self._raw(TXT_2HEIGHT)
        else:  # DEFAULT SIZE: NORMAL
            self._raw(TXT_NORMAL)
        # Type
        if type.upper() == "B":
            self._raw(TXT_BOLD_ON)
            self._raw(TXT_UNDERL_OFF)
        elif type.upper() == "U":
            self._raw(TXT_BOLD_OFF)
            self._raw(TXT_UNDERL_ON)
        elif type.upper() == "U2":
            self._raw(TXT_BOLD_OFF)
            self._raw(TXT_UNDERL2_ON)
            self._raw(TXT_ITALIC_OFF)
        elif type.upper() == "BU":
            self._raw(TXT_BOLD_ON)
            self._raw(TXT_UNDERL_ON)
        elif type.upper() == "BU2":
            self._raw(TXT_BOLD_ON)
            self._raw(TXT_UNDERL2_ON)
        elif type.upper == "NORMAL":
            self._raw(TXT_BOLD_OFF)
            self._raw(TXT_UNDERL_OFF)
        # Font
        if font.upper() == "B":
            self._raw(TXT_FONT_B)
        else:  # DEFAULT FONT: A
            self._raw(TXT_FONT_A)
        # Align
        if align.upper() == "CENTER":
            self._raw(TXT_ALIGN_CT)
        elif align.upper() == "RIGHT":
            self._raw(TXT_ALIGN_RT)
        elif align.upper() == "LEFT":
            self._raw(TXT_ALIGN_LT)


    def cut(self, mode=''):
        """ Cut paper """
        # Fix the size between last line and cut
        # TODO: handle this with a line feed
        self._raw("\n\n\n\n\n\n")
        if mode.upper() == "PART":
            self._raw(PAPER_PART_CUT)
        else:  # DEFAULT MODE: FULL CUT
            self._raw(PAPER_FULL_CUT)


    def cashdraw(self, pin):
        """ Send pulse to kick the cash drawer """
        if pin == 2:
            self._raw(CD_KICK_2)
        elif pin == 5:
            self._raw(CD_KICK_5)
        else:
            raise CashDrawerError()


    def hw(self, hw):
        """ Hardware operations """
        if hw.upper() == "INIT":
            self._raw(HW_INIT)
        elif hw.upper() == "SELECT":
            self._raw(HW_SELECT)
        elif hw.upper() == "RESET":
            self._raw(HW_RESET)
        else:  # DEFAULT: DOES NOTHING
            pass


    def control(self, ctl):
        """ Feed control sequences """
        if ctl.upper() == "LF":
            self._raw(CTL_LF)
        elif ctl.upper() == "FF":
            self._raw(CTL_FF)
        elif ctl.upper() == "CR":
            self._raw(CTL_CR)
        elif ctl.upper() == "HT":
            self._raw(CTL_HT)
        elif ctl.upper() == "VT":
            self._raw(CTL_VT)
            
            
    # Helper functions to facilitate printing
    def format_date(self, date):
        string = str(date['date']) + '/' + str(date['month']) + '/' + str(date['year']) + ' ' + str(date['hour']) + ':' + "%02d" % date['minute']
        return string
    
    def write(self, string, rcolstr=None, align="left"):
        """Write simple text string. Remember \n for newline where applicable.
        rcolstr is a righthand column that may be added
        (e.g. a price on a receipt). Be aware that when rcolstr is
        used newline(s) may only be a part of rcolstr, and only as
        the last character(s)."""
        if align != "left" and len(string) < self.width:
            blanks = 0
            if align == "right":
                blanks = self.width - len(string.rstrip("\n"))
            if align == "center":
                blanks = (self.width - len(string.rstrip("\n"))) / 2
            string = " " * blanks + string
    
        if not rcolstr:
            try:
                self.text(string)
            except:
                logger.error('No pude escribir', exc_info=1)
                raise
        else:
            rcolStrRstripNewline = rcolstr.rstrip("\n")
            if "\n" in string or "\n" in rcolStrRstripNewline:
                raise ValueError("When using rcolstr in POSprinter.write only newline at the end of rcolstr is allowed and not in string (the main text string) it self.")
            # expand string
            lastLineLen = len(string) % self.width + len(rcolStrRstripNewline)
            if lastLineLen > self.width:
                numOfBlanks = (self.width - lastLineLen) % self.printer.width
                string += numOfBlanks * " "
                lastLineLen = len(string) % self.width + len(rcolStrRstripNewline)
            if lastLineLen < self.width:
                numOfBlanks = self.width - lastLineLen
                string += " " * numOfBlanks
            try:
                self.text(string + rcolstr)
            except:
                logger.error('No pude escribir', exc_info=1)
                raise
    
    def lineFeed(self, times=1, cut=False):
        """Write newlines and optional cut paper"""
        while times:
            try:
                self.text("\n")
            except:
                raise
            times -= 1
        if cut:
            try:
                self.cut('part')
            except:
                raise
    
    def lineFeedCut(self, times=6, cut=True):
        """Enough line feed for the cut to be beneath the previously printed text etc."""
        try:
            self.lineFeed(times, cut)
        except:
            raise
    
    def font(self, font='a'):
        if font == 'a':
            self._raw('\x1b\x4d\x01')
            self.width = self.widthA
        else:
            self._raw('\x1b\x4d\x00')
            self.width = self.widthB
    
    def bold(self, bold=True):
        if bold:
            self._raw('\x1b\x45\x01')
        else:
            self._raw('\x1b\x45\x00')
    
    def decimal(self, number):
        return "%0.2f" % float(number)
    
    def printImgFromFile(self, filename, resolution="high", align="center", scale=None):
        """Print an image from a file.
        resolution may be set to "high" or "low". Setting it to low makes the image a bit narrow (90x60dpi instead of 180x180 dpi) unless scale is also set.
        align may be set to "left", "center" or "right".
        scale resizes the image with that factor, where 1.0 is the full width of the paper."""
        try:
            from PIL import Image
            # Open file and convert to black/white (colour depth of 1 bit)
            img = Image.open(filename).convert("1")
            self._printImgFromPILObject(img, resolution, align, scale)
        except:
            raise
    
    def _printImgFromPILObject(self, imgObject, resolution="high", align="center", scale=None):
        """The object must be a Python ImageLibrary object, and the colordepth should be set to 1."""
        try:
            # If a scaling factor has been indicated
            if scale:
                assert type(scale) == float
                if scale > 1.0 or scale <= 0.0:
                    raise ValueError, "scale: Scaling factor must be larger than 0.0 and maximum 1.0"
                # Give a consistent output regardless of the resolution setting
                scale *= self.pxWidth / float(imgObject.size[0])
                if resolution is "high":
                    scaleTuple = (scale * 2, scale * 2)
                else:
                    scaleTuple = (scale, scale * 2 / 3.0)
                # Convert to binary colour depth and resize
                imgObjectB = imgObject.resize([ int(scaleTuple[i] * imgObject.size[i]) for i in range(2) ]).convert("1")
            else:
                # Convert to binary colour depth
                imgObjectB = imgObject.convert("1")
            # Convert to a pixel access object
            imgMatrix = imgObjectB.load()
            width = imgObjectB.size[0]
            height = imgObjectB.size[1]
            # Print it
            self._printImgMatrix(imgMatrix, width, height, resolution, align)
        except:
            raise
    
    def _printImgMatrix(self, imgMatrix, width, height, resolution, align):
            """Print an image as a pixel access object with binary colour."""
            if resolution == "high":
                scaling = 24
                currentpxWidth = self.pxWidth * 2
            else:
                scaling = 8
                currentpxWidth = self.pxWidth
            if width > currentpxWidth:
                raise ValueError("Image too wide. Maximum width is configured to be " + str(currentpxWidth) + "pixels. The image is " + str(width) + " pixels wide.")
            tmp = ''
            for yScale in range(-(-height / scaling)):
                # Set mode to hex and 8-dot single density (60 dpi).
                if resolution == "high":
                    outList = [ "0x1B", "0x2A", "0x21" ]
                else:
                    outList = [ "0x1B", "0x2A", "0x00" ]
                # Add width to the communication to the printer. Depending on the alignment we count that in and add blank vertical lines to the outList
                if align == "left":
                    blanks = 0
                if align == "center":
                    blanks = (currentpxWidth - width) / 2
                if align == "right":
                    blanks = currentpxWidth - width
                highByte = (width + blanks) / 256
                lowByte = (width + blanks) % 256
                outList.append(hex(lowByte))
                outList.append(hex(highByte))
                if resolution == "high":
                    blanks *= 3
                if align == "left":
                    pass
                if align == "center":
                    for i in range(blanks):
                        outList.append(hex(0))
                if align == "right":
                    for i in range(blanks):
                        outList.append(hex(0))
                for x in range(width):
                    # Compute hex string for one vertical bar of 8 dots (zero padded from the bottom if necessary).
                    binStr = ""
                    for y in range(scaling):
                        # Indirect zero padding. Do not try to extract values from images beyond its size.
                        if (yScale * scaling + y) < height:
                            binStr += "0" if imgMatrix[x, yScale * scaling + y] == 255 else "1"
                        # Zero padding
                        else:
                            binStr += "0"
                    outList.append(hex(int(binStr[0:8], 2)))
                    if resolution == "high":
                        outList.append(hex(int(binStr[8:16], 2)))
                        outList.append(hex(int(binStr[16:24], 2)))
                for element in outList:
                    try:
                        tmp += chr(int(element, 16))
                    except:
                        raise
    
            self.write(tmp)
