import discord
import configparser
from ThermalPrinter import ThermalPrinter
import atexit
from datetime import datetime
import pytz
import re

client = discord.Client()
printer = None
prevMsg = None

def findUrls(inputString):
    regex=r"\b((?:https?://)?(?:(?:www\.)?(?:[\da-z\.-]+)\.(?:[a-z]{2,6})|(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)|(?:(?:[0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,7}:|(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,5}(?::[0-9a-fA-F]{1,4}){1,2}|(?:[0-9a-fA-F]{1,4}:){1,4}(?::[0-9a-fA-F]{1,4}){1,3}|(?:[0-9a-fA-F]{1,4}:){1,3}(?::[0-9a-fA-F]{1,4}){1,4}|(?:[0-9a-fA-F]{1,4}:){1,2}(?::[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:(?:(?::[0-9a-fA-F]{1,4}){1,6})|:(?:(?::[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(?::[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(?:ffff(?::0{1,4}){0,1}:){0,1}(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])|(?:[0-9a-fA-F]{1,4}:){1,4}:(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])))(?::[0-9]{1,4}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])?(?:/[\w\.-]*)*/?)\b"

    matches = re.findall(regex, inputString)
    return matches

def exit_handler():
    printer.close()


def fixTimeZone(badTime):
    utcZone = pytz.timezone('Etc/UTC')
    correctZone = pytz.timezone('America/New_York')
    time = datetime.combine(badTime.date(), badTime.time(), utcZone)
    timeRight = time.astimezone(correctZone)
    return timeRight


def handlePrintEvent(message):
    global prevMsg
    
    if prevMsg is None or prevMsg.channel.id != message.channel.id:
        tempString = " #" + message.channel.name + " "
        tempString = tempString.center(printer.lineWidth, '-')
        printer.addLineFeed()
        printer.addText(tempString)
    
    if prevMsg is None or prevMsg.author.id != message.author.id:
        printer.addLineFeed()
        uname = message.author.nick if message.author.nick else message.author.name
        printer.addText(uname, wrap=False)
        printer.addLineFeed()

        time = fixTimeZone(message.created_at)
        printer.addText(time.strftime("%b. %d, %I:%M%p"))
        printer.addLineFeed()
        printer.addLineFeed()

    if message.clean_content:
        changed = False
        if len(message.clean_content) > 280:
            printer.selectFontB()
            changed = True

        printer.addText(message.clean_content)

        if changed:
            printer.selectFontA()

        printer.addLineFeed()
        
        urls = findUrls(message.clean_content)
        if len(urls):
            for ii in range(len(urls)):
                if urls[ii].lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif')):
                    printer.addImage(urls[ii])
                    printer.addLineFeed()

    if len(message.attachments) > 0:
        for ii in range(len(message.attachments)):
            printer.addImage(message.attachments[ii].url)
            printer.addLineFeed()

    printer.flush()
    prevMsg = message


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    if printer.ready: #  message.guild.id == 714670784051806218 and 
        handlePrintEvent(message)


if __name__ == "__main__":
    atexit.register(exit_handler)

    config = configparser.ConfigParser()
    config.read('./config.ini')

    port = config['printerInfo']['serialPort']
    baudRate = int(config['printerInfo']['baudRate'])
    flowControl = config['printerInfo']['flowControl']

    printer = ThermalPrinter(port=port, baud=baudRate,
                             flowControl=flowControl, cut=False)
    printer.initialize()

    client.run(config['basicInfo']['apiKey'])
