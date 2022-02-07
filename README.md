```
    ____       _       __            ____        __ 
   / __ \_____(_)___  / /____  _____/ __ )____  / /_
  / /_/ / ___/ / __ \/ __/ _ \/ ___/ __  / __ \/ __/
 / ____/ /  / / / / / /_/  __/ /  / /_/ / /_/ / /_  
/_/   /_/  /_/_/ /_/\__/\___/_/  /_____/\____/\__/  
                                                     
```
A Discord bot that logs messages to a thermal printer.

## Setup
### Discord Setup
I'm really rushing to put this `Readme` together, so just follow any other discord bot tutorial for creating a bot account and getting the API Key

### Bot Setup
#### Installation
Uhh, this is really annoying, as I decided to use a bunch of different libraries. You will need:
* Discord.py
* PIL
* pyserial
* requests
* textwrap
* pytz

And maybe others, I forget which need to be explicitly installed and which are installed by default. 

#### Config File
Put the information for your thermal printer in `config.ini` (Baud rate and serial port), as well as your Discord API key that you obtained earlier.

## Running the bot
Once that's all set up, simply execute `python3 main.py` and you'll be good to go.
