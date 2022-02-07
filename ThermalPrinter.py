import textwrap
from PIL import Image
import serial
import math
import unicodedata
import sys


class ThermalPrinter:
    def __init__(self, port, baud=9600, dsrdtr=True, cut=False):
        self.ready = False                                          # Printer is not ready
        self.serialPort = port                                      # Set port name
        self.baud = baud                                            # Set baud rate
        self.hardwareFlow = dsrdtr                                  # Set flow control
        self.cut = cut                                              # Auto-cut after flush
        self.lineWidth = 42                                         # Default width for 3 1/8" paper
        self.hiResDots = 512                                        # Full res image width
        self.loResDots = 256                                        # Half res image width

    # Basic Functions
    def initialize(self):
        self.clearBuffer()                                                                # Init print buffer
        self.ser = serial.Serial(port=self.serialPort, baudrate=self.baud,                # Open serial port
                                 dsrdtr=self.hardwareFlow, xonxoff= not self.hardwareFlow)# ''
        self.ready = True                                                                 # Printer is ready

    def close(self):
        self.ser.close()                            # Close serial port
        self.ready = False                          # Printer is not ready

    def addRaw(self, raw):
        self.printBuffer += raw                     # Append data to buffer

    def clearBuffer(self):
        self.printBuffer = b''                      # Set buffer to an empty buffer

    def flush(self):
        if self.cut: self.addCut()                  # Handle cutting on flush
        self.ser.write(self.printBuffer)            # Output buffer
        self.clearBuffer()                          # Clear internal buffer

    def logPrintBuffer(self):
        sys.stdout.buffer.write(self.printBuffer)   # Write raw data to terminal

    # Printer management
    def selectFontA(self):
        self.addRaw(b'\x1B\x4D\x00')    # Select character font (ESC M 0)
        self.addRaw(b'\x1B\x33\x3C')    # Set line spacing (ESC 3 60)
        self.lineWidth = 42             # Update word wrap variable

    def selectFontB(self):
        self.addRaw(b'\x1B\x4D\x01')    # Select character font (ESC M 1)
        self.addRaw(b'\x1B\x33\x2A')    # Set line spacing (ESC 3 42)
        self.lineWidth = 56             # Update word wrap variable

    def initializePrinter(self):
        self.clearBuffer()              # Clear internal buffer
        self.addRaw(b'\x1B\x40')        # Initialize printer (Esc @)
        self.lineWidth = 42             # Reset word wrap variable
        self.flush()                    # Send command to printer

    # Standard printing operations
    def addText(self, text, wrap=True):
        normalized = unicodedata.normalize('NFKD', text)                # Convert special characters to normal
        normalized = normalized.encode('ascii', 'ignore').decode()      # Convert characters to ascii and store

        if wrap:
            self.addRaw(bytes(wrapText(normalized, self.lineWidth), encoding='ascii'))   # Handle wrap
        else:
            self.addRaw(bytes(normalized, encoding='ascii'))     # Add text!

    def addLineFeed(self):
        self.addRaw(b'\n')                          # Self explanatory :P

    def addCut(self):
        self.addRaw(b'\x1D\x56\x42\x00')            # Select cut mode and cut paper (GS V 66 0)

    def addImage(self, inImage):
        mode = 0                                    # Select either full or half-res mode
        image = Image.open(inImage)                 # Open the image

        newWidth = None                     
        if image.width < self.hiResDots:            # If the image is smaller than full-res width:
            if image.width <= self.loResDots:           # If the image is smaller than quarter-res width:
                newWidth = image.width
                mode = 3                                    # Select quarter-res mode
            elif image.width > self.hiResDots * (3/4):  # Round up image halfway between two resolutions
                newWidth = self.hiResDots
                mode = 0
            else:                                       #Round down to quarter-res
                newWidth = self.loResDots
                mode = 3
        else:
            newWidth = self.hiResDots

        newWidth -= newWidth % 8                                            # Make sure width is multiple of 8 bits
        newHeight = math.floor((image.height / image.width) * newWidth)     # Scale height, preserving aspect ratio

        image = image.resize((newWidth, newHeight))                         # Scale image
        image = image.convert("1")                                          # Convert to black and white

        xL = (newWidth >> 3) & 0xFF                 # Get low x byte
        xH = ((newWidth >> 3) >> 8) & 0xFF          # Get high x byte
        yL = newHeight & 0xFF                       # Get low y byte
        yH = (newHeight >> 8) & 0xFF                # Get high y byte

        self.addRaw(b'\x1D\x76\x30')                # GS v 0
        self.addRaw(bytes([mode, xL, xH, yL, yH]))  # print mode, lo x byte, hi x byte, lo y byte, hi x byte

        for y in range((256*yH) + yL):                          # Loop over image vertically
            for x in range((256*xH) + xL):                      # Loop over image horizontally
                a = 0
                for i in range(8):
                    pxdat = image.getpixel(((x*8)+i, y)) < 64   # IDK what any of this does, I didn't write it
                    a = a | pxdat << 7 >> i
                self.addRaw(bytes([int(a) % 256]))              # Add bytes to print buffer


def wrapText(text, width):
    lines = text.splitlines(True)
    wrapped = ""
    for line in lines:
        if line == '\n':
            wrapped += '\n'
            continue
        wrapped += textwrap.fill(line, width, replace_whitespace=False)
        if line[-1] == '\n':
            wrapped += '\n'
    return wrapped
