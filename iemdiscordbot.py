from html.parser import HTMLParser
from bs4 import BeautifulSoup
import time
import datetime as dt
import requests
import re
import discord
import asyncio

refreshRate = 15 # seconds
pauseBetweenMessages = 1 # seconds

def parseMessages(data):

    for messages in data:
        message = messages['message']

        soup = BeautifulSoup(message, features="html.parser")
        for script in soup(["script", "style"]):
            script.extract() # take out any script and styling

        text = soup.get_text()

        # break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines())
        # break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)

        messages['message'] = text

    return data


async def main():

    botserver = client.get_guild(927052295072534530)

    prevEndOfSeq = 0

    while True:

        rooms = ['botstalk']

        for room in rooms:
            r = requests.get(f"https://weather.im/iembot-json/room/{room}?seqnum={prevEndOfSeq}")

            if r.status_code == 200:

                data = r.json()['messages']

                if not (len(data) == 0):

                    prevEndOfSeq = data[-1]['seqnum']

                    data = parseMessages(data)

                    for message in data:
                        #await asyncio.sleep(pauseBetweenMessages)

                        text = message['message']
                        message['channels'] = ['all-messages']

                        t = dt.datetime.strptime(message['ts'], '%Y-%m-%d %H:%M:%S')
                        now = dt.datetime.utcnow()
                        diff = now - t

                        fTime = t.strftime('%H:%M:%S')

                        # FILTERS --------------------------------------------------

                        bannedStrings = ["Climate Report:", "Routine pilot report",
                        "Terminal Aerodrome Forecast", "SIGMET", "Zone Forecast Package", "Area Forecast Discussion"]

                        subs = [
                        # tornado watches
                        [r"(?<!(expires|cancels) )(tornado watch|tornado: possible)", f"**\g<0>**"],

                        # tornado warnings or word tornado
                        [r"(?<!(expires|cancels) )(tornado warning|tornado: radar indicated|tornado: observed|tornado(?!( watch|: possible)))", f"**\g<0>**"],

                        # severe thunderstorm watches
                        [r"(?<!(expires|cancels) )severe thunderstorm watch", f"**\g<0>**"],

                        # severe thunderstorm warnings
                        [r"(?<!(expires|cancels) )(severe thunderstorm warning|severe thunderstorm(?! watch))",    f"**\g<0>**"],

                        # winter storm/weather watches
                        [r"(?<!(expires|cancels) )winter storm watch", f"**\g<0>**"],

                        # winter storm/weather warningss
                        [r"(?<!(expires|cancels) )(winter storm warning|winter storm(?! watch)|winter weather advisory|winter weather(?! watch))", f"**\g<0>**"],

                        # Mesoscale Discussion
                        [r"Mesoscale Discussion \#\d+", f"**\g<0>**"],

                        # hail size
                        [r"hail:?\s*(of\s*)?[><+-]?\d+\.?\d*\s?(inches|inch|in)(hail)?", f"**\g<0>**"],

                        # snowfall amounts
                        [r"(heavy\s*)?snow:?\s*(of\s*)?[><+-]?\d+\.?\d*\s?(inches|inch|in|)(of)?(snow)?", f"**\g<0>**"],

                        # damage
                        [r"DMG|damage", f"**\g<0>**"],

                        # match windspeed
                        [r"(sust |sustained |peak )?(gust |wind |winds )?(of )?M?(\d{2}G)?\d+\.?\d*\s?(mph|kts|kt|knots|knot)", f"**\g<0>**"],
                        ]

                        # PRINTING ----------------------------------------------------------
                        # filter banned topics
                        if not (any(x in text for x in bannedStrings) or text.startswith("METAR")):
                            message['channels'].append('filtered')

                            if any(x in text.lower() for x in ["tornado"]):
                                message['channels'].append('tornado')

                            if any(x in text.lower() for x in ['severe thunderstorm', 'hail', 'strong thunderstorms', 'mesoscale discussion', 'flood']):
                                message['channels'].append('severe')

                            if any(x in text.lower() for x in ['winter storm', 'snow', 'ice', 'freezing rain', 'winter weather', 'freeze', 'wind chill']):
                                message['channels'].append('winter')

                            if any(x in text.lower() for x in ['wildfire', 'fire', 'smoke']):
                                message['channels'].append('wildfire')

                            if any(x in text.lower() for x in ['flood', 'flash flood', 'flooding']):
                                message['channels'].append('flooding')

                            if any(x in text.lower() for x in ['reports', 'dmg', 'damage']):
                                message['channels'].append('reports')

                        # make highlight substitutions
                        for sub in subs:
                            text = re.sub(sub[0], sub[1], text, flags=re.I)

                        # do not post unfiltered for now
                        message['channels'].remove("all-messages")

                        #if "filtered" in message["channels"]:
                            #message['channels'].remove("filtered")

                        # PRINTING ----------------------------------------------------------
                        if (diff < dt.timedelta(minutes=1)):
                            for channelName in message['channels']:
                                channel = discord.utils.get(botserver.channels, name=channelName)
                                text = f"`{fTime}`: {text}"
                                #print(message['channels'], text)
                                await channel.send(text)
                                time.sleep(pauseBetweenMessages)


            else:
                print(f"{room}: HTTP Error: {r.status_code}")

        await asyncio.sleep(refreshRate)



#discord stuff

client = discord.Client()

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    await main()


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.author.id == 396730242460418058 and message.content == "!stop":
        print("Was told to stop by austin")
        exit();



with open("token.config", "r") as file:
    for line in file:
        token = line


client.run(token)
