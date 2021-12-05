# import urllib library
from urllib.request import urlopen

# for making the pfp image round
from PIL import Image, ImageDraw

# import stuff
import sys, time, pygame, json, threading, traceback, urllib, os


# setInterval for python
class setInterval:
    def __init__(self, interval, action):
        self.interval = interval
        self.action = action
        self.stopEvent = threading.Event()
        thread = threading.Thread(target=self.__setInterval)
        thread.start()

    def __setInterval(self):
        nextTime = time.time() + self.interval
        while not self.stopEvent.wait(nextTime - time.time()):
            nextTime += self.interval
            self.action()

    def cancel(self):
        self.stopEvent.set()


# Converts a number to a human readable format
# Eg. 1000 -> 1k, 15,500 -> 15.5k, etc.
# Code from https://stackoverflow.com/a/45846841/15871490
def human_format(num):
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    # add more suffixes if you need them
    return '%.2f%s' % (num, ['', 'K', 'M', 'G', 'T', 'P'][magnitude])


# Read the config
configFile = open("config.json", "r")
config = json.loads(configFile.read())

# Auth and youtube channel id stuff
youtubeKey = config["api_key"]
youtubeUser = config["youtube"]["user_id"]
pfpRoundness = config["youtube"]["profile_pic_roundness"]
rawNumbers = config["counter"]["raw_numbers"]

# here we store our subcount and
# user data
sub_count = 0
sub_name = "Loading..."
api_calls = 0

# for the pfp
pfp_img = None
pfp_img_size = 0, 0
pfp_downloaded = False

# store the URL in url as
# parameter for urlopen
api_url = f"https://www.googleapis.com/youtube/v3/channels?part=snippet%2CcontentDetails%2Cstatistics&id={youtubeUser}&key={youtubeKey}"


# helper function to add rounded corners to the pfp
# code from: https://stackoverflow.com/a/11291419/15871490
def add_corners(im, rad):
    circle = Image.new('L', (rad * 2, rad * 2), 0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, rad * 2, rad * 2), fill=255)
    alpha = Image.new('L', im.size, 255)

    w, h = im.size

    alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
    alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
    alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
    alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))

    im.putalpha(alpha)
    return im


def fetch_image(path):
    global pfp_downloaded, pfp_img

    try:
        im = Image.open(path)
        im = add_corners(im, int(pfpRoundness))
        im.save(path)

        pfp_img = pygame.image.load(path)
        pfp_downloaded = True
    except:
        pass


def fetch_count():
    global sub_count, sub_name, api_calls, pfp_downloaded, pfp_img, pfp_img_size

    # store the response of URL
    response = urlopen(api_url)

    # storing the JSON response
    # from url in data
    data_json = json.loads(response.read())

    # set the subcount
    sub_count = data_json["items"][0]["statistics"]["subscriberCount"]

    # some channels dont have a custom url
    # so if the specified channel doesnt have a channel
    # url, use it's channel title instead
    try:
        sub_name = data_json["items"][0]["snippet"]["customUrl"]
    except:
        sub_name = data_json["items"][0]["snippet"]["title"]

    api_calls += 1

    # Download it once
    if not pfp_downloaded:
        urllib.request.urlretrieve(
            data_json["items"][0]["snippet"]["thumbnails"]["default"]["url"],
            "temp/profile_pic.png")

        pfp_img_size = data_json["items"][0]["snippet"]["thumbnails"][
            "default"]["width"], data_json["items"][0]["snippet"][
                "thumbnails"]["default"]["height"]

        # load pfp
        fetch_image("temp/profile_pic.png")

    # print the json response
    print(f"Subscriber count: {sub_count}")


# count update thread
job = setInterval(5, fetch_count)


# define a main function
def main():
    global pfp_img

    try:
        os.remove("temp/profile_pic.png")
    except:
        pass

    # initialize the pygame module
    pygame.init()

    # # load and set the logo
    # logo = pygame.image.load("logo32x32.png")
    # pygame.display.set_icon(logo)
    pygame.display.set_caption("Live YouTube Subscriber Count (by yeppiidev)")

    # create a surface on screen that has the size of 240 x 180
    screen = pygame.display.set_mode((480, 320))

    # define a variable to control the main loop
    running = True

    fontBig = pygame.font.Font(os.path.join("res", "Montserrat-Bold.ttf"), 55)
    fontNorm = pygame.font.Font(os.path.join("res", "Montserrat-Bold.ttf"), 20)
    fontSmol = pygame.font.Font(os.path.join("res", "Montserrat-Bold.ttf"), 15)

    # main loop
    while running:
        try:
            # event handling, gets all event from the event queue
            for event in pygame.event.get():
                # only do something if the event is of type QUIT
                if event.type == pygame.QUIT:
                    # change the value to False, to exit the main loop
                    running = False

                    global job
                    # stop the counter and exit app
                    job.cancel()
                    sys.exit()

            width, height = pygame.display.get_surface().get_size()

            count_str = f"{human_format(int(sub_count)) if not rawNumbers else format(int(sub_count), ',')}"
            channel_str = f"youtube.com/{sub_name}"

            screen.fill((0, 0, 0))

            tw1, th1 = fontBig.size(count_str)
            tw2, th2 = fontNorm.size(channel_str)

            count_str_Surf = fontBig.render(count_str, True, (235, 230, 69))
            channel_str_Surf = fontNorm.render(channel_str, True,
                                               (255, 255, 255))
            apicount_str_Surf = fontSmol.render(f"API Calls: {str(api_calls)}",
                                                True, (255, 255, 255))

            screen.blit(count_str_Surf, (width / 2 - tw1 / 2, height / 2 + 10))
            screen.blit(channel_str_Surf,
                        (width / 2 - tw2 / 2, height / 2 + 80))
            screen.blit(apicount_str_Surf, (10, height - 30))

            if not pfp_img is None:
                screen.blit(pfp_img, (width / 2 - pfp_img_size[0] / 2,
                                      height / 2 - 40 - pfp_img_size[1] / 2))

            pygame.display.flip()

        except Exception as ex:
            print(traceback.format_exc())
            print(f"Fatal error: {ex}")

            job.cancel()
            sys.exit()


# run the main function only if this module is executed as the main script
# (if you import this as a module then nothing is executed)
if __name__ == "__main__":
    main()
