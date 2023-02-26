from html.parser import HTMLParser
from bs4 import BeautifulSoup
import time
import datetime as dt
import requests
import re
import discord
import asyncio
import sys
import yaml

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


def parseConfig():
    try:
        text_file = sys.argv[1]
    except:
        print("Please provide a valid file name")
        exit()
    else:
        try:
            with open(text_file, "r") as fp:
                config = yaml.safe_load(fp)
                return config

        except yaml.YAMLError as err:
            print("YAML Error: " + err)
            exit()




async def main():

    config = parseConfig()

    botserver = client.get_guild(config["server_id"])

    prevEndOfSeq = {}

    while True:

        for room in config["rooms"]:

            try:
                seqnum = prevEndOfSeq[room]
            except:
                seqnum = 0

            try:
                r = requests.get(f"https://weather.im/iembot-json/room/{room}?seqnum={seqnum}")
            except: 
                print("Accessing website failed: room `" + room + "` and seq num `" + seqnum + "`")
                continue

            if r.status_code == 200:

                discord_message = ""

                data = r.json()['messages']

                if not (len(data) == 0):

                    prevEndOfSeq[room] = data[-1]['seqnum']

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
                        if (not any(x in text for x in config["message"]["must_not_contain"])) and any(x in text for x in config["message"]["must_contain"]):

                            # make highlight substitutions
                            for sub in config["message"]["subs"]:
                                text = re.sub(sub["regex"], sub["replacement"], text, flags=re.I)

                            # PRINTING ----------------------------------------------------------
                            if (diff < dt.timedelta(minutes=1)):
                                discord_message += f"`{fTime}`: {text}\n"
                
                if not discord_message == "":
                    channel = client.get_channel(config["channel_id"])
                    await channel.send(discord_message)
                    await asyncio.sleep(pauseBetweenMessages)

            else:
                print(f"{room}: HTTP Error: {r.status_code}")

        await asyncio.sleep(refreshRate)



#discord stuff

intents = discord.Intents.default()

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    await main()


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.author.id == 396730242460418058 and message.content == "!stop":
        print("Was told to stop by austin.")
        exit();



with open("token.config", "r") as file:
    for line in file:
        token = line



client.run(token)
