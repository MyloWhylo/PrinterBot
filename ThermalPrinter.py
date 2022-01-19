import textwrap
from PIL import Image
import serial
import requests
import math
import unicodedata
import sys


class ThermalPrinter:
    def __init__(self, port, baud=9600, flowControl="dsrdtr", paperWidth=3.125, margin=0.15, dpi=180, lineWidth=42, cut=False):
        self.printBuffer = b''
        self.ready = False
        # assumes margin and width are in fractional inches (e.g. 2.25)
        self.dots = math.floor((paperWidth - (margin*2)) * dpi)
        self.serialPort = port
        self.baud = baud
        self.flowHardware = True if flowControl == "dsrdtr" else False
        self.flowSoftware = not self.flowHardware
        self.cut = cut
        self.lineWidth = lineWidth
        self.fontA = True

    def initialize(self):
        self.ser = serial.Serial(port=self.serialPort, baudrate=self.baud,
                                 dsrdtr=self.flowHardware, xonxoff=self.flowSoftware)
        self.ready = True

    def clearBuffer(self):
        self.printBuffer = b''

    def addCut(self):
        self.printBuffer += b'\x1D\x56\x42\x00'  # GS V 66 0

    def selectFontA(self):
        self.printBuffer += b'\x1B\x4D\x00'  # ESC M 0
        self.addRaw(b'\x1B\x33\x3C')
        self.lineWidth = 42

    def selectFontB(self):
        self.printBuffer += b'\x1B\x4D\x01'  # ESC M 1
        self.addRaw(b'\x1B\x33\x2A')
        self.lineWidth = 56

    def logPrintBuffer(self):
        sys.stdout.buffer.write(self.printBuffer)

    def close(self):
        self.ser.close()
        self.ready = False

    def flush(self):
        if self.cut:
            self.addCut()
        self.ser.write(self.printBuffer)
        self.clearBuffer()

    def addRaw(self, raw):
        self.printBuffer += raw

    def addText(self, text, wrap=True):
        normalized = unicodedata.normalize('NFKD', text)
        normalized = normalized.encode('ascii', 'ignore').decode()

        if wrap:
            self.printBuffer += bytes(wrapText(normalized,
                                      self.lineWidth), encoding='ascii')
        else:
            self.printBuffer += bytes(normalized, encoding='ascii')

    def addLineFeed(self):
        self.printBuffer += b'\n'

    def addImage(self, url):
        mode = 0

        response = requests.get(url, stream=True)
        image = Image.open(response.raw)

        newWidth = image.width if image.width < self.dots else self.dots
        if image.width < (self.dots / 2): mode = 3
        newHeight = math.floor((image.height / image.width) * newWidth)

        image = image.resize((newWidth, newHeight))
        image = image.convert("1")

        xL = (newWidth//8) % 256
        xH = (newWidth//8) // 256
        yL = newHeight % 256
        yH = newHeight // 256

        temp = b'\x1D\x76\x30'
        temp += bytes([mode])   # m
        temp += bytes([xL])  # xL
        temp += bytes([xH])  # xH
        temp += bytes([yL])  # yL
        temp += bytes([yH])  # yH

        for y in range((256*yH) + yL):
            for x in range((256*xH) + xL):
                a = 0
                for i in range(8):
                    pxdat = image.getpixel(((x*8)+i, y)) < 64
                    a = a | pxdat << 7 >> i
                temp += bytes([int(a) % 256])
        self.printBuffer += temp


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
