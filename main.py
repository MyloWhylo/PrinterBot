import discord
import configparser
from ThermalPrinter import ThermalPrinter
import atexit
from datetime import datetime
import pytz
import re
import requests

client = discord.Client()
printer = None
prevMsg = None
doPrinting = True

blockedChannels = [809244814977662987, 809244835877486614]

def findURLs(inputString):
    regex = r"\b((?:https?://)?(?:(?:www\.)?(?:[\da-z\.-]+)\.(?:[a-z]{2,6})|(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)|(?:(?:[0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,7}:|(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,5}(?::[0-9a-fA-F]{1,4}){1,2}|(?:[0-9a-fA-F]{1,4}:){1,4}(?::[0-9a-fA-F]{1,4}){1,3}|(?:[0-9a-fA-F]{1,4}:){1,3}(?::[0-9a-fA-F]{1,4}){1,4}|(?:[0-9a-fA-F]{1,4}:){1,2}(?::[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:(?:(?::[0-9a-fA-F]{1,4}){1,6})|:(?:(?::[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(?::[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(?:ffff(?::0{1,4}){0,1}:){0,1}(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])|(?:[0-9a-fA-F]{1,4}:){1,4}:(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])))(?::[0-9]{1,4}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])?(?:/[\w\.-]*)*/?)\b"

    return re.findall(regex, inputString)


def isValidImage(url):
    return url.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif'))


def exit_handler():
    printer.close()


def addImageFromURL(url):
    response = requests.get(url, stream=True)
    printer.addImage(response.raw)


def fixTimeZone(badTime):
    utcZone = pytz.timezone('Etc/UTC')
    correctZone = pytz.timezone('America/New_York')
    time = datetime.combine(badTime.date(), badTime.time(), utcZone)
    timeRight = time.astimezone(correctZone)
    return timeRight


def handlePrintEvent(message):
    global prevMsg
    global doPrinting
    global printer

    if prevMsg is None:
        guildHeader = channelHeader = authorHeader = True
    else:
        guildHeader = prevMsg.guild.id != message.guild.id
        channelHeader = prevMsg.channel.id != message.channel.id
        authorHeader = prevMsg.author.id != message.author.id

    if guildHeader or authorHeader:
        printer.addLineFeed()

    if guildHeader:
        tempString = " " + message.guild.name + " "
        tempString = tempString.center(printer.lineWidth, '=')
        printer.addText(tempString)
        printer.addLineFeed()

    if channelHeader:
        tempString = " #" + message.channel.name + " "
        tempString = tempString.center(printer.lineWidth, '-')
        printer.addText(tempString)
        printer.addLineFeed()

    if authorHeader:
        uname = message.author.nick if message.author.nick is not None else message.author.name
        time = fixTimeZone(message.created_at)
        printer.addText(uname + ", " + time.strftime("%b. %d, %I:%M%p") + ":")
        printer.addLineFeed()

    if message.clean_content:
        if len(message.clean_content) > 280:
            printer.selectFontB()
            printer.addText(message.clean_content)
            printer.selectFontA()
        else:
            printer.addText(message.clean_content)

        printer.addLineFeed()

    urls = findURLs(message.clean_content)
    if urls:
        for ii in range(len(urls)):
            if isValidImage(urls[ii]):
                addImageFromURL(urls[ii])
                printer.addLineFeed()

    if len(message.attachments) > 0:
        for ii in range(len(message.attachments)):
            if isValidImage(message.attachments[ii].url):
                addImageFromURL(message.attachments[ii].url)
                printer.addLineFeed()

    if doPrinting:
        printer.flush()
    prevMsg = message


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    global doPrinting
    global printer
    
    if message.channel.id in blockedChannels:
        return

    if message.clean_content == "??pausePrinting":
        doPrinting = False
        print("Paused.")
    elif message.clean_content == "??resumePrinting":
        doPrinting = True
        print("Resumed.")
        printer.flush()
    elif printer.ready:
        handlePrintEvent(message)


if __name__ == "__main__":
    atexit.register(exit_handler)

    config = configparser.ConfigParser()
    config.read('./config.ini')

    port = config['printerInfo']['serialPort']
    baudRate = int(config['printerInfo']['baudRate'])
    flowControl = config['printerInfo']['flowControl']

    printer = ThermalPrinter(port=port, baud=baudRate,
                             dsrdtr=True, cut=False)
    printer.initialize()

    client.run(config['basicInfo']['apiKey'])
