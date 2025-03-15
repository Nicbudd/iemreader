#!/usr/bin/env python

from html.parser import HTMLParser
from bs4 import BeautifulSoup
import time
import datetime as dt
import requests
import re

refreshRate = 5 # in seconds

class colors:
    black = '\033[30m'
    red = '\033[31m'
    green = '\033[32m'
    yellow = '\033[33m'
    blue = '\033[34m'
    purple = '\033[35m'
    cyan = '\033[36m'
    white = '\033[97m'

    emer1 = '\033[0m\033[1;41;97m'
    emer2 = '\033[0m\033[1;45;97m'


    blackBG = '\033[0m\033[40m'
    redBG = '\033[0m\033[41m'
    greenBG = '\033[0m\033[42m'
    yellowBG = '\033[0m\033[43m'
    blueBG = '\033[0m\033[44m'
    purpleBG = '\033[0m\033[45m'
    cyanBG = '\033[0m\033[46m'
    whiteBG = '\033[0m\033[107m'

    bold = '\033[1m'
    underline = '\033[4m'

    end = '\033[0m'

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


def main():

    firstRun = True

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
                        text = message['message']

                        t = dt.datetime.strptime(message['ts'], '%Y-%m-%d %H:%M:%S')
                        t = t.replace(tzinfo=dt.timezone.utc)
                        now = dt.datetime.now(dt.UTC)
                        diff = now - t

                        fTime = t.strftime('%H:%M:%S')

                        # FILTERS --------------------------------------------------

                        bannedStrings = ["PIREP", "PIRUS",  "Climate Report:", "Routine pilot report",
                        "Terminal Aerodrome Forecast", "SIGMET", "Zone Forecast Package", "Area Forecast Discussion"]

                        subs = [
                        # tornado emergency
                        [r"(?<!(expires|cancels) )tornado emergency", f"{colors.emer1}TORNADO EMERGENCY{colors.end}"],

                        # tornado watches
                        [r"(?<!(expires|cancels) )(tornado watch|tornado: possible)", f"{colors.red}\\g<0>{colors.end}"],

                        # tornado warnings or word tornado
                        [r"(?<!(expires|cancels) )(tornado warning|tornado: radar indicated|tornado: observed|tornado(?!( watch|: possible| emergency)))", f"{colors.redBG}\\g<0>{colors.end}"],


                        # severe thunderstorm watches
                        [r"(?<!(expires|cancels) )severe thunderstorm watch", f"{colors.yellow}\\g<0>{colors.end}"],

                        # severe thunderstorm warnings
                        [r"(?<!(expires|cancels) )(severe thunderstorm warning|severe thunderstorm(?! watch))",    f"{colors.yellowBG}\\g<0>{colors.end}"],

                        # winter storm/weather watches
                        [r"(?<!(expires|cancels) )winter storm watch", f"{colors.blue}\\g<0>{colors.end}"],

                        # winter storm/weather warningss
                        [r"(?<!(expires|cancels) )(winter storm warning|winter storm(?! watch)|winter weather advisory|winter weather(?! watch))", f"{colors.blueBG}\\g<0>{colors.end}"],

                        # Mesoscale Discussion
                        [r"Mesoscale Discussion \#\d+", f"{colors.greenBG}\\g<0>{colors.end}"],

                        # hail size
                        [r"hail:?\s*(of\s*)?[><+-]?\d+\.?\d*\s?(inches|inch|in)(hail)?", f"{colors.cyanBG}\\g<0>{colors.end}"],

                        # snowfall amounts
                        [r"(heavy\s*)?snow:?\s*(of\s*)?[><+-]?\d+\.?\d*\s?(inches|inch|in|)(of)?(snow)?", f"{colors.blueBG}\\g<0>{colors.end}"],

                        # damage
                        [r"DMG|damage", f"{colors.purpleBG}\\g<0>{colors.end}"],

                        # match windspeed
                        [r"(sust |sustained |peak )?(gust |wind |winds )?(of )?M?(\d{2}G)?\d+\.?\d*\s?(mph|kts|kt|knots|knot)", f"{colors.green}\\g<0>{colors.end}"],

                        # match inches
                        #[r"\d+\.?\d*\s?(inches|inch|in)", f"{colors.green}\g<0>{colors.end}"],


                        # reports
                        [r"(\] )(.* reports ((tstm|wnd|gst|non-tstm|gust|snow|hail) )*)", f"\\g<1>{colors.purple}\\g<2>{colors.end}"],

                        # locale boxes
                        [r"\[[^\]]*(GYX|BOX|BOS|BTV|NH|ME|VT|MA|MASS|CT|RI|Manchester,? NH)[^\[]*\]", f"{colors.whiteBG}{colors.black}\\g<0>{colors.end}"],

                        # locale in other places
                        [r"(?<=[^\w\[])(GYX|BOX|BOS|BTV|NH|ME|VT|MA|MASS|CT|RI|Manchester,? NH)(?=[^\w\]])", f"{colors.whiteBG}{colors.black}\\g<1>{colors.end}"],

                        ]

                        # get rid of banned topics
                        if any(x in text for x in bannedStrings):
                            continue

                        # get rid of banned metar
                        if re.search(r"^METAR", text) is not None:
                            continue

                        # make coloration substitutions
                        for sub in subs:
                            text = re.sub(sub[0], sub[1], text, flags=re.I)

                        # ----------------------------------------------------------

                        # PRINTING
                        if firstRun and (diff < dt.timedelta(minutes=15)):
                            print(f"{colors.bold}{colors.underline}{fTime}{colors.end}: {text}")

                        else:
                            print(f"{colors.bold}{colors.underline}{fTime}{colors.end}: {text}")

            else:
                print(f"{room}: HTTP Error: {r.status_code}")


        firstRun = False

        time.sleep(refreshRate)

if __name__ == "__main__":
    main()
