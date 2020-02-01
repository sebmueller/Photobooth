#!/usr/bin/python3
## import sys
import os
import pyudev
import psutil

from PIL import Image  # image manipulation for Overlay
import time  # timing
import picamera  # camera driver
import shutil  # file io access like copy
from datetime import datetime  # datetime routine
import RPi.GPIO as GPIO  # gpio access
import subprocess  # call external scripts
from transitions import Machine  # state machine
import configparser  # parsing config file
import logging  # logging functions
import cups  # connection to cups printer driver
import usb  # check if printer is connected and turned on
from wand.image import Image as image  # image manipulation lib

# get the real path of the script
REAL_PATH = os.path.dirname(os.path.realpath(__file__))

"""
Class containing the single Photos
"""


class PictureOnCard:

    # init method
    def __init__(self, pictureNumber):
        self.__resizeX = 800  # defaults
        self.__resizeY = 600  # defaults
        self.__rotate = 0
        self.__posX = 0
        self.__posY = 0
        self.__fileNamePrefix = ""
        self.__pictureNumber = pictureNumber
        self.__image = ""
        self.__color = ""

    # list of getter and setter
    def __getResizeX(self):
        return self.__resizeX

    def __setResizeX(self, x):
        self.__resizeX = x

    resizeX = property(__getResizeX, __setResizeX)

    def __getResizeY(self):
        return self.__resizeY

    def __setResizeY(self, y):
        self.__resizeY = y

    resizeY = property(__getResizeY, __setResizeY)

    def __getRotate(self):
        return self.__rotate

    def __setRotate(self, y):
        self.__rotate = y

    rotate = property(__getRotate, __setRotate)

    def __getPosX(self):
        return self.__posX

    def __setPosX(self, x):
        self.__posX = x

    posX = property(__getPosX, __setPosX)

    def __getPosY(self):
        return self.__posY

    def __setPosY(self, y):
        self.__posY = y

    posY = property(__getPosY, __setPosY)

    def __getFileNamePrefix(self):
        return self.__fileNamePrefix

    def __setFileNamePrefix(self, name):
        self.__fileNamePrefix = name

    fileNamePrefix = property(__getFileNamePrefix, __setFileNamePrefix)

    def __getPictureNumber(self):
        return self.__pictureNumber

    def __setPictureNumber(self, number):
        self.__pictureNumber = number

    pictureNumber = property(__getPictureNumber, __setPictureNumber)

    def __getFileName(self):
        return self.__fileNamePrefix + '_' + str(self.__pictureNumber) + '.jpg'

    def __setFileName(self):
        pass

    fileName = property(__getFileName, __setFileName)

    def __getImage(self):
        return self.__image

    def __setImage(self, img):
        self.__image = img

    img = property(__getImage, __setImage)

    def __getColor(self):
        return self.__color

    def __setColor(self, color):
        self.__color = color

    color = property(__getColor, __setColor)

    # string return method
    def __str__(self):
        return "Picture: " + str(self.fileName) + " size: " + str(self.resizeX) + " / " + str(self.resizeY) + \
               " rot: " + str(self.rotate) + " pos: " + str(self.posX) + " / " + str(self.posY) + " - color " + str(self.color)

    # process the image
    def ProcessImage(self):
        self.img.resize(self.resizeX, self.resizeY)
        self.img.rotate(self.rotate)

    # Load the image from the saved filename
    def LoadImage(self):
        self.img = image(filename=self.fileName)


"""
class containing the photo card
"""


class PhotoCard:

    # init method
    def __init__(self):
        self.__sizeX = 1868  # default for Canon Selphy printer
        self.__sizeY = 1261  # default for Canon Selphy printer
        self.__cardTemplate = ""
        self.__cardFileName = ""
        self.__picCount = 0
        self.__fileNamePrefix = ""
        self.__pictures = []  # list for single pictures on card
        self.__cardImage = ""
        self.__layoutInForeground = False

    # list of getter and setter
    def __getSizeX(self):
        return self.__sizeX

    def __setSizeX(self, x):
        self.__sizeX = x

    sizeX = property(__getSizeX, __setSizeX)

    def __getSizeY(self):
        return self.__sizeY

    def __setSizeY(self, y):
        self.__sizeY = y

    sizeY = property(__getSizeY, __setSizeY)

    def __getPicCount(self):
        return self.__picCount

    def __setPicCount(self, piccount):
        # if piccount is different to current, clear photoobject list and create a new list
        if piccount != self.__picCount:
            self.__pictures.clear()

            # create a new list of photoobjects
            for i in range(1, piccount + 1):
                self.__pictures.append(PictureOnCard(i))

        self.__picCount = piccount

    piccount = property(__getPicCount, __setPicCount)

    def __getLayoutInForeground(self):
        return self.__layoutInForeground

    def __setLayoutInForeground(self, foreground):
        self.__layoutInForeground = foreground

    layoutInForeground = property(__getLayoutInForeground, __setLayoutInForeground)

    def __getCardTemplate(self):
        return self.__cardTemplate

    def __setCardTemplate(self, name):
        self.__cardTemplate = name

    templateFileName = property(__getCardTemplate, __setCardTemplate)

    def __getFileNamePrefix(self):
        return self.__fileNamePrefix

    def __setFileNamePrefix(self, name):
        self.__fileNamePrefix = name
        self.cardFileName = self.fileNamePrefix + '_card' + '.jpg'
        for x in self.__pictures:
            x.fileNamePrefix = name

    fileNamePrefix = property(__getFileNamePrefix, __setFileNamePrefix)

    def __getCardFileName(self):
        return self.__cardFileName

    def __setCardFileName(self, name):
        self.__cardFileName = name

    cardFileName = property(__getCardFileName, __setCardFileName)

    def __getPicture(self):
        return self.__pictures

    def __setPicture(self):
        pass

    picture = property(__getPicture, __setPicture)

    def __getCardImage(self):
        return self.__cardImage

    def __setCardImage(self):
        pass

    cardImage = property(__getCardImage, __setCardImage)

    # reload the card background image
    def loadImageTemplate(self):
        self.__cardImage = image(filename=self.templateFileName).clone()

    # create an empty card, if template is in foreground
    def createEmptyCard(self):
        self.__cardImage = image(width=self.sizeX, height=self.sizeY)

    # create the card
    def processCard(self):
        #if layout in foreground, the template is overlaied at last
        if self.layoutInForeground:
            self.createEmptyCard()

        else:
            self.loadImageTemplate()

        # composite all photos to card
        for i in range(0, self.piccount):
            self.__cardImage.composite(self.picture[i].img, self.picture[i].posX,
                                       self.picture[i].posY)

        # if Layout is in foreground, overlay it last
        if self.layoutInForeground:
            self.__cardImage.composite(image(filename=self.templateFileName).clone(), 0, 0)

        self.__cardImage.resize(int(1868), int(1261))

    # string return method
    def __str__(self):
        return str(self.piccount) + " photos on Template: " + str(self.templateFileName) + " save as: " + str(
            self.cardFileName)


"""
Class controlling the photobooth
"""


class Photobooth:
    # define state machine for taking photos
    FSMstates = ['PowerOn', 'Start', 'CountdownPhoto', 'TakePhoto', 'ShowPhoto', 'CreateCard', 'ShowCard', 'PrintCard',
                 'RefillPaper', 'RefillInk', 'Restart']

    def __init__(self):
        # create the card objects
        self.layout = [PhotoCard(), PhotoCard()]

        self.initStateMachine()

        logging.debug("Read Config File")
        self.readConfiguration()

        logging.debug("Config GPIO")
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin_button_right, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.pin_button_left, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.pin_button_right, GPIO.FALLING, callback=self.Button2pressed, bouncetime=500)
        GPIO.add_event_detect(self.pin_button_left, GPIO.FALLING, callback=self.Button1pressed, bouncetime=500)

        logging.debug("Set TimeStamp for Buttons")
        self.time_stamp_button1 = time.time()
        self.time_stamp_button2 = time.time()

        self.button1active = False
        self.button2active = False

        logging.debug("Setup Camera")
        # Setup Camera
        try:
            self.camera = picamera.PiCamera()
        except:
            logging.CRITICAL("error initializing the camera - exiting")
            raise SystemExit

        self.camera.resolution = (self.photo_w, self.photo_h)
        self.camera.hflip = self.flip_screen_h
        self.camera.vflip = self.flip_screen_v
        self.startpreview()

        self.photonumber = 1

        self.cycleCounter = 0

        # load the Logo of the Photobooth and display it
        self.overlayscreen_logo = self.overlay_image_transparency(self.screen_logo, 0, 5)

        # find the USB Drive, if connected
        self.PhotoCopyPath = self.GetMountpoint()

        # path for saving photos on usb drive
        if self.PhotoCopyPath is not None:
            self.PhotoCopyPath = self.PhotoCopyPath + "/Fotos"
            logging.debug("Photocopypath = " + self.PhotoCopyPath)
            if not os.path.exists(self.PhotoCopyPath):
                logging.debug("os.mkdir(self.PhotoCopyPath)")
                os.mkdir(self.PhotoCopyPath)
        else:
            logging.debug("self.PhotoCopyPath not Set -> No USB Drive Found")

        # find the USB Drive with card layout configuration
        self.CardConfigFile = self.GetMountpoint()

        # read card config data
        if self.CardConfigFile is not None:
            self.CardConfigFile = self.CardConfigFile + '/Fotobox/card.ini'
            logging.debug("Config file for Card creating:")
            logging.debug(self.CardConfigFile)

        else:
            self.CardConfigFile = os.path.join(REAL_PATH, 'Templates/Default/card.ini')
            logging.debug("Default Config file for Card creating:")
            logging.debug(self.CardConfigFile)

        # read card configuration if config exists
        if not os.path.exists(self.CardConfigFile):
            self.CardConfigFile = os.path.join(REAL_PATH, 'Templates/Default/card.ini')

        # load the Card Layout
        self.readCardConfiguration(self.CardConfigFile)

        # Start the Application
        self.on_enter_PowerOn()

    # ends the Application
    def __del__(self):
        logging.debug("__del__ Function")
        self.stoppreview()
        self.camera.close()
        GPIO.setmode(GPIO.BCM)
        GPIO.cleanup()
        del self.imagetemplate1
        del self.imagetemplate2

    # Init the State machine controlling the Photobooth
    def initStateMachine(self):
        logging.debug("Init State Machine")
        self.machine = Machine(model=self, states=self.FSMstates, initial='PowerOn', ignore_invalid_triggers=True)
        self.machine.add_transition(source='PowerOn', dest='PowerOn',
                                    trigger='Button1')  # power on self test - check if printer is conected
        self.machine.add_transition(source='PowerOn', dest='Start',
                                    trigger='PrinterFound')  # printer is on -> goto start
        self.machine.add_transition(source='Start', dest='CountdownPhoto', trigger='Button1')
        self.machine.add_transition(source='Start', dest='CountdownPhoto', trigger='Button2')
        self.machine.add_transition(source='CountdownPhoto', dest='TakePhoto',
                                    trigger='CountdownPhotoTimeout')  # timeout
        self.machine.add_transition(source='TakePhoto', dest='ShowPhoto', trigger='None')
        self.machine.add_transition(source='ShowPhoto', dest='CountdownPhoto', trigger='Button1')  # N=N - Again
        self.machine.add_transition(source='ShowPhoto', dest='CountdownPhoto', trigger='Button2')  # N++ - Next Picture
        self.machine.add_transition(source='ShowPhoto', dest='CreateCard', trigger='MaxPics')  #
        self.machine.add_transition(source='CreateCard', dest='ShowCard',
                                    trigger='None')  # N==4 amount of Pictures reached
        self.machine.add_transition(source='ShowCard', dest='PrintCard', trigger='Button1')  # print
        # self.machine.add_transition(source='ShowCard', dest='Start', trigger='Button2')  # do not print
        # self.machine.add_transition(source='PrintCard', dest='Start', trigger='PrintDone')  # print done
        self.machine.add_transition(source='ShowCard', dest='Restart', trigger='Button2')  # do not print
        self.machine.add_transition(source='PrintCard', dest='Restart', trigger='PrintDone')  # print done

        self.machine.add_transition(source='RefillPaper', dest='Restart',
                                    trigger='Button1')  # Refill Paper on printer
        self.machine.add_transition(source='RefillPaper', dest='Restart',
                                    trigger='Button2')  # Refill Paper on printer
        self.machine.add_transition(source='RefillInk', dest='Start',
                                    trigger='Button1')  # Refill Ink on printer
        self.machine.add_transition(source='RefillInk', dest='Start',
                                    trigger='Button2')  # Refill Ink on printer
        self.machine.add_transition(source='PrintCard', dest='RefillPaper',
                                    trigger='PaperEmpty')  # Refill Paper on printer
        self.machine.add_transition(source='PrintCard', dest='RefillInk',
                                    trigger='InkEmpty')  # Refill Ink on printer

    # Read the Card Creating Configuration
    def readCardConfiguration(self, path):
        logging.debug("Read card Config File")
        self.cardconfig = configparser.ConfigParser()
        self.cardconfig.sections()

        if path is not None:
            logging.debug("start reading")
            self.cardconfig.read(path)

            # layout 1 configuration
            self.layout[0].piccount = int(self.cardconfig.get("Layout1", "piccount", fallback="0"))
            self.layout[0].templateFileName = os.path.join(os.path.split(path)[0],
                                                           self.cardconfig.get("Layout1", "cardtemplate", fallback="0"))

            self.layout[0].layoutInForeground = self.cardconfig.getboolean("Layout1", "layout_in_foreground", fallback=False)

            # manipulation of photos for Layout 1
            for i in range(0, self.layout[0].piccount):
                self.layout[0].picture[i].resizeX = int(
                    self.cardconfig.get("Layout1", "resize_image_x_" + str(i + 1), fallback="0"))
                self.layout[0].picture[i].resizeY = int(
                    self.cardconfig.get("Layout1", "resize_image_y_" + str(i + 1), fallback="0"))
                self.layout[0].picture[i].rotate = int(
                    self.cardconfig.get("Layout1", "rotate_image_" + str(i + 1), fallback="0"))
                self.layout[0].picture[i].posX = int(
                    self.cardconfig.get("Layout1", "position_image_x_" + str(i + 1), fallback="0"))
                self.layout[0].picture[i].posY = int(
                    self.cardconfig.get("Layout1", "position_image_y_" + str(i + 1), fallback="0"))
                self.layout[0].picture[i].color = self.cardconfig.get("Layout1", "color_image_" + str(i + 1), fallback="color")

                logging.debug(self.layout[0].picture[i])

            logging.debug(self.layout[0])

            # layout 2 configuration
            self.layout[1].piccount = int(self.cardconfig.get("Layout2", "piccount", fallback="0"))
            self.layout[1].templateFileName = os.path.join(os.path.split(path)[0],
                                                           self.cardconfig.get("Layout2", "cardtemplate", fallback="0"))

            self.layout[1].layoutInForeground = self.cardconfig.getboolean("Layout2", "layout_in_foreground", fallback=False)

            # manipulation of photos for Layout 2
            for i in range(0, self.layout[1].piccount):
                self.layout[1].picture[i].resizeX = int(
                    self.cardconfig.get("Layout2", "resize_image_x_" + str(i + 1), fallback="0"))
                self.layout[1].picture[i].resizeY = int(
                    self.cardconfig.get("Layout2", "resize_image_y_" + str(i + 1), fallback="0"))
                self.layout[1].picture[i].rotate = int(
                    self.cardconfig.get("Layout2", "rotate_image_" + str(i + 1), fallback="0"))
                self.layout[1].picture[i].posX = int(
                    self.cardconfig.get("Layout2", "position_image_x_" + str(i + 1), fallback="0"))
                self.layout[1].picture[i].posY = int(
                    self.cardconfig.get("Layout2", "position_image_y_" + str(i + 1), fallback="0"))
                self.layout[1].picture[i].color = self.cardconfig.get("Layout2", "color_image_" + str(i + 1),
                                                                      fallback="color")

                logging.debug(self.layout[1].picture[i])

            logging.debug(self.layout[1])

            self.imagetemplate1 = image(filename=self.layout[0].templateFileName)
            self.imagetemplate2 = image(filename=self.layout[1].templateFileName)

    # read the global configuration, folders, resolution....
    def readConfiguration(self):
        logging.debug("Read Config File")
        self.config = configparser.ConfigParser()
        self.config.sections()
        self.config.read(os.path.join(REAL_PATH, 'config.ini'))

        if self.config.getboolean("Debug", "debug", fallback=True) == True:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.WARNING)

        self.printPicsEnable = self.config.getboolean("Debug", "print", fallback=True)

        if self.printPicsEnable == False:
            logging.debug("Printing pics disabled")

        self.photo_abs_file_path = os.path.join(REAL_PATH, self.config.get("Paths", "photo_path", fallback="Photos/"))
        self.screens_abs_file_path = os.path.join(REAL_PATH,
                                                  self.config.get("Paths", "screen_path", fallback="Screens/"))
        self.pin_button_left = int(self.config.get("InOut", "pin_button_left", fallback="23"))
        self.pin_button_right = int(self.config.get("InOut", "pin_button_right", fallback="24"))
        self.photo_w = int(self.config.get("Resolution", "photo_w", fallback="3280"))
        self.photo_h = int(self.config.get("Resolution", "photo_h", fallback="2464"))
        self.screen_w = int(self.config.get("Resolution", "screen_w", fallback="1024"))
        self.screen_h = int(self.config.get("Resolution", "screen_h", fallback="600"))
        self.flip_screen_h = self.config.getboolean("Resolution", "flip_screen_h", fallback=False)
        self.flip_screen_v = self.config.getboolean("Resolution", "flip_screen_v", fallback=False)
        self.screen_turnOnPrinter = os.path.join(self.screens_abs_file_path,
                                                 self.config.get("Screens", "screen_turn_on_printer",
                                                                 fallback="ScreenTurnOnPrinter.png"))
        self.screen_logo = os.path.join(self.screens_abs_file_path,
                                        self.config.get("Screens", "screen_logo", fallback="ScreenLogo.png"))
        self.screen_choose_layout = os.path.join(self.screens_abs_file_path,
                                                 self.config.get("Screens", "screen_Choose_Layout",
                                                                 fallback="ScreenChooseLayout.png"))
        self.screen_countdown_0 = os.path.join(self.screens_abs_file_path,
                                               self.config.get("Screens", "screen_countdown_0",
                                                               fallback="ScreenCountdown0.png"))
        self.screen_countdown_1 = os.path.join(self.screens_abs_file_path,
                                               self.config.get("Screens", "screen_countdown_1",
                                                               fallback="ScreenCountdown1.png"))
        self.screen_countdown_2 = os.path.join(self.screens_abs_file_path,
                                               self.config.get("Screens", "screen_countdown_2",
                                                               fallback="ScreenCountdown2.png"))
        self.screen_countdown_3 = os.path.join(self.screens_abs_file_path,
                                               self.config.get("Screens", "screen_countdown_3",
                                                               fallback="ScreenCountdown3.png"))
        self.screen_countdown_4 = os.path.join(self.screens_abs_file_path,
                                               self.config.get("Screens", "screen_countdown_4",
                                                               fallback="ScreenCountdown4.png"))
        self.screen_countdown_5 = os.path.join(self.screens_abs_file_path,
                                               self.config.get("Screens", "screen_countdown_5",
                                                               fallback="ScreenCountdown5.png"))
        self.screen_black = os.path.join(self.screens_abs_file_path,
                                         self.config.get("Screens", "screen_black",
                                                         fallback="ScreenBlack.png"))
        self.screen_again_next = os.path.join(self.screens_abs_file_path,
                                              self.config.get("Screens", "screen_again_next",
                                                              fallback="ScreenAgainNext.png"))
        self.screen_wait = os.path.join(self.screens_abs_file_path,
                                        self.config.get("Screens", "screen_wait",
                                                        fallback="ScreenWait.png"))
        self.screen_print = os.path.join(self.screens_abs_file_path,
                                         self.config.get("Screens", "screen_print",
                                                         fallback="ScreenPrint.png"))
        self.screen_print_again = os.path.join(self.screens_abs_file_path,
                                               self.config.get("Screens", "screen_print_again",
                                                               fallback="ScreenPrintagain.png"))
        self.screen_change_ink = os.path.join(self.screens_abs_file_path,
                                              self.config.get("Screens", "screen_change_ink",
                                                              fallback="ScreenChangeInk.png"))
        self.screen_change_paper = os.path.join(self.screens_abs_file_path,
                                                self.config.get("Screens", "screen_change_paper",
                                                                fallback="ScreenChangePaper.png"))


        self.screen_photo = []

        for i in range(0, 9):
            self.screen_photo.append(os.path.join(self.screens_abs_file_path,
                                               self.config.get("Screens", "screen_photo_" + str(i + 1),
                                                               fallback="ScreenPhoto" + str(i + 1) + ".png")))


    def setCameraColor(self, color):
        if color == "bw":
            self.camera.color_effects = (128, 128)  # turn camera to black and white
        elif color == "sepia":
            self.camera.color_effects = (100, 150)  # turn camera to black and white
        else:
            self.camera.color_effects = None


    # Button1 callback function. Actions depends on state of the Photobooth state machine

    def Button1pressed(self, event):
        logging.debug("Button1pressed")
        time_now = time.time()

        #if button was pressed
        if self.button1active:
            if (time_now - self.time_stamp_button1) < 3.0:
                return

        self.button1active = True

        # wait until button is released
        while not GPIO.input(self.pin_button_left):
            time.sleep(0.1)
            # if button pressed longer than 5 sec -> shutdown
            if (time.time() - time_now) > 5:
                subprocess.call("sudo poweroff", shell=True)
                return

        time.sleep(0.2)

        # if in PowerOnState - ignore Buttons
        if self.state == "PowerOn":
            return

        # if in PrintCard State - ignore Buttons
        if self.state == "PrintCard":
            return

        # debounce the button
        if (time_now - self.time_stamp_button1) >= 0.5:
            logging.debug("Debounce time reached")
            # from state start -> choose layout 1
            if self.state == "Start":
                logging.debug("State == Start -> Set Photonumbers")
                self.MaxPhotos = self.layout[0].piccount
                self.current_Layout = 1
                self.photonumber = 1

            logging.debug("self.button1 start")
            self.Button1()
            logging.debug("self.button1 ready -> Set new TimeStamp")
            self.time_stamp_button1 = time.time()
            self.button1active = False
            self.button2active = False

    # Button2 callback function. Actions depends on state of the Photobooth state machine
    def Button2pressed(self, event):
        logging.debug("Button2pressed")
        time_now = time.time()

        if self.button2active:
            if (time_now - self.time_stamp_button2) < 3.0:
                return

        self.button2active = True

        # wait until button is released
        while not GPIO.input(self.pin_button_right):
            time.sleep(0.1)

        time.sleep(0.2)

        # if in PowerOnState - ignore Buttons
        if self.state == "PowerOn":
            return

        # if in PrintCard State - ignore Buttons
        if self.state == "PrintCard":
            return

        # debounce the button
        if (time_now - self.time_stamp_button2) >= 0.5:
            logging.debug("Debounce time reached")

            # from state start -> choose layout 2
            if self.state == "Start":
                logging.debug("State == Start -> Set Photonumbers")
                self.MaxPhotos = self.layout[1].piccount
                self.current_Layout = 2
                self.photonumber = 1

            # from state Show Photo -> increase Photonumber
            if self.state == 'ShowPhoto':
                logging.debug("State == ShowPhoto -> increase Photonumber")
                self.photonumber += 1

                # last photo reached
                if self.photonumber > self.MaxPhotos:
                    logging.debug("maxpics")
                    self.MaxPics()
                    logging.debug("self.button2 ready -> Set new TimeStamp")
                    self.time_stamp_button2 = time.time()
                    return

            logging.debug("self.button2 start")
            self.Button2()
            logging.debug("self.button2 ready -> Set new TimeStamp")
            self.time_stamp_button2 = time.time()
            self.button1active = False
            self.button2active = False

    # create a small preview of the layout for the first screen
    def createCardLayoutPreview(self):
        logging.debug("createCardLayoutPreview")

        logging.debug(self.layout[0])
        logging.debug(self.layout[0].piccount)

        # Load Preview Pics
        for i in range(0, self.layout[0].piccount):
            logging.debug(self.layout[0].picture[i])
            self.layout[0].picture[i].img = image(
                filename = os.path.join(REAL_PATH, 'Media/demo' + str(i + 1) + '.jpg'))
            self.layout[0].picture[i].ProcessImage()


        # Load Preview Pics
        for i in range(0, self.layout[1].piccount):
            logging.debug(self.layout[1].picture[i])
            self.layout[1].picture[i].img = image(
                filename = os.path.join(REAL_PATH, 'Media/demo' + str(i + 1) + '.jpg'))
            self.layout[1].picture[i].ProcessImage()

        self.layout[0].processCard()
        self.layout[1].processCard()

        self.layout[0].cardImage.resize(int(1868 / 8), int(1261 / 8))
        self.layout[1].cardImage.resize(int(1868 / 8), int(1261 / 8))

        screen = image(width=self.screen_w, height=self.screen_h)

        # create screen
        screen.composite(self.layout[0].cardImage, 131, self.screen_h - 184)
        screen.composite(self.layout[1].cardImage, self.screen_w - int(1868 / 8) - 131, self.screen_h - 184)

        # save screen to file for displaying
        screen.save(filename=self.screen_choose_layout)

    # This function captures the photo
    def taking_photo(self, photo_number):
        logging.debug("Taking Photo")
        # get the filename also for later use
        self.lastfilename = self.layout[self.current_Layout - 1].picture[photo_number - 1].fileName

        ## take a picture
        self.camera.capture(self.lastfilename)
        logging.debug("Photo (" + str(photo_number) + ") saved: " + self.lastfilename)

    # Power On Check State
    # check if printer is connected and turned on
    def on_enter_PowerOn(self):
        logging.debug("now on_enter_PowerOn")
        self.overlay_screen_turnOnPrinter = -1

        if not self.CheckPrinter():
            logging.debug("no printer found")
            self.overlay_screen_turnOnPrinter = self.overlay_image_transparency(self.screen_turnOnPrinter, 0, 3)

        while not self.CheckPrinter():
            time.sleep(2)

        logging.debug("printer found")
        self.PrinterFound()

    # leave Power On Check State
    def on_exit_PowerOn(self):
        logging.debug("now on_exit_PowerOn")

        # create the preview of the layouts
        self.createCardLayoutPreview()

        # remove overlay "turn on printer", if still on display
        self.remove_overlay(self.overlay_screen_turnOnPrinter)

    # Start State -> Show initail Screen
    def on_enter_Start(self):
        self.button1active = False
        self.button2active = False
        
        logging.debug("now on_enter_Start")
        self.overlay_screen_blackbackground = self.overlay_image(self.screen_black, 0, 2)
        self.overlay_choose_layout = self.overlay_image_transparency(self.screen_choose_layout, 0, 7)

    # leave start screen
    def on_exit_Start(self):
        logging.debug("now on_exit_Start")
        # on start of every photosession, create an unique filename, containing date and time
        self.layout[0].fileNamePrefix = self.get_base_filename_for_images()
        self.layout[1].fileNamePrefix = self.get_base_filename_for_images()
        self.remove_overlay(self.overlay_choose_layout)

    # countdown to zero and take picture
    def on_enter_CountdownPhoto(self):
        logging.debug("now on_enter_CountdownPhoto")

        #set the picture color
        self.setCameraColor(self.layout[self.current_Layout - 1].picture[self.photonumber - 1].color)

        # print the countdown
        self.overlay_screen_Countdown = self.overlay_image_transparency(self.screen_countdown_5, 0, 7)
        time.sleep(1)
        self.remove_overlay(self.overlay_screen_Countdown)
        self.overlay_screen_Countdown = self.overlay_image_transparency(self.screen_countdown_4, 0, 7)
        time.sleep(1)
        self.remove_overlay(self.overlay_screen_Countdown)
        self.overlay_screen_Countdown = self.overlay_image_transparency(self.screen_countdown_3, 0, 7)
        time.sleep(1)
        self.remove_overlay(self.overlay_screen_Countdown)
        self.overlay_screen_Countdown = self.overlay_image_transparency(self.screen_countdown_2, 0, 7)
        time.sleep(1)
        self.remove_overlay(self.overlay_screen_Countdown)
        self.overlay_screen_Countdown = self.overlay_image_transparency(self.screen_countdown_1, 0, 7)
        time.sleep(1)
        self.remove_overlay(self.overlay_screen_Countdown)
        self.overlay_screen_Countdown = self.overlay_image_transparency(self.screen_countdown_0, 0, 7)
        time.sleep(1)
        self.remove_overlay(self.overlay_screen_Countdown)

        # countdown finished
        self.CountdownPhotoTimeout()

    def on_exit_CountdownPhoto(self):
        logging.debug("now on_exit_CountdownPhoto")

    # take a pciture
    def on_enter_TakePhoto(self):
        logging.debug("now on_enter_TakePhoto")
        self.taking_photo(self.photonumber)
        self.to_ShowPhoto()

    def on_exit_TakePhoto(self):
        logging.debug("now on_exit_TakePhoto")
        # turn off camera preview
        self.stoppreview()

    # show the picture
    def on_enter_ShowPhoto(self):
        logging.debug("now on_enter_ShowPhoto")

        # show last photo and menu
        self.overlay_screen_black = self.overlay_image(self.screen_black, 0, 5)
        self.overlay_last_photo = self.overlay_image(self.lastfilename, 0, 6)
        self.overlay_photo_number = self.overlay_image_transparency(self.screen_photo[self.photonumber - 1], 0, 8)

        # log filename
        logging.debug(str(self.lastfilename))

        # copy photo to USB Drive
        if self.PhotoCopyPath is not None:
            logging.debug(str(self.PhotoCopyPath))
            logging.debug(os.path.basename(str(self.lastfilename)))
            logging.debug((str(self.PhotoCopyPath)) + '/' + os.path.basename(str(self.lastfilename)))
            shutil.copyfile((str(self.lastfilename)),
                            ((str(self.PhotoCopyPath)) + '/' + os.path.basename(str(self.lastfilename))))

        logging.debug("start resizing")
        logging.debug("self.photonumber")
        logging.debug(self.photonumber)
        logging.debug("self.current_Layout")
        logging.debug(self.current_Layout)

        # load the image to the layoutobject and process (resize / rotate the image)
        self.layout[self.current_Layout - 1].picture[self.photonumber - 1].LoadImage()
        self.layout[self.current_Layout - 1].picture[self.photonumber - 1].ProcessImage()

        self.overlay_again_next = self.overlay_image_transparency(self.screen_again_next, 0, 7)

        logging.debug("finish resizing")

    # state show photo
    def on_exit_ShowPhoto(self):
        logging.debug("now on_exit_ShowPhoto")
        self.remove_overlay(self.overlay_screen_black)
        self.remove_overlay(self.overlay_last_photo)
        self.remove_overlay(self.overlay_again_next)
        self.remove_overlay(self.overlay_photo_number)
        self.startpreview()

    # create photocard
    def on_enter_CreateCard(self):
        logging.debug("now on_enter_CreateCard")
        logging.debug("self.MaxPhotos")
        logging.debug(self.MaxPhotos)

        self.overlay_wait = self.overlay_image_transparency(self.screen_wait, 0, 7)

        # name of saved card for later use
        self.cardfilename = self.layout[self.current_Layout - 1].cardFileName

        # create the card
        self.layout[self.current_Layout - 1].processCard()

        # save the card to disk
        self.layout[self.current_Layout - 1].cardImage.save(filename=self.layout[self.current_Layout - 1].cardFileName)

        self.to_ShowCard()

    def on_exit_CreateCard(self):
        logging.debug("now on_exit_CreateCard")
        self.remove_overlay(self.overlay_wait)

    # show the photocard
    def on_enter_ShowCard(self):
        logging.debug("now on_enter_ShowCard")

        self.overlay_last_card = self.overlay_image(self.cardfilename, 0, 6)
        self.overlay_screen_print = self.overlay_image_transparency(self.screen_print, 0, 7)

        logging.debug("copying")
        # copy card to photo folder
        if self.PhotoCopyPath is not None:
            logging.debug("Copy Card to USB Drive")
            shutil.copy2(str(self.cardfilename), str(self.PhotoCopyPath))

    def on_exit_ShowCard(self):
        logging.debug("now on_exit_ShowCard")
        self.startpreview()
        self.remove_overlay(self.overlay_last_card)
        self.remove_overlay(self.overlay_screen_print)

    # print the photocard
    def on_enter_PrintCard(self):
        logging.debug("now on_enter_PrintCard")
        # restart camera
        self.stoppreview()
        self.startpreview()

        if self.printPicsEnable == False:
            logging.debug("print enable = false")

        # print photo?
        if self.printPicsEnable == True:
            logging.debug("print enable = true")

            # connect to cups
            conn = cups.Connection()
            printername = list(conn.getPrinters().keys())

            print(printername)
    
            # use first printer
            logging.debug("Printer Name: " + printername[0])
            conn.enablePrinter(printername[0])
    
            # check printer state
            printerstate = conn.getPrinterAttributes(printername[0], requested_attributes=["printer-state-message"])
    
            # if printer in error state ->
            if str(printerstate).find("error:") > 0:
                logging.debug(str(printerstate))
                conn.cancelAllJobs(printername[0], my_jobs=True, purge_jobs=True)
                if str(printerstate).find("06") > 0:
                    logging.debug("goto refill ink")
                    self.InkEmpty()
                    return
                if str(printerstate).find("03") > 0:
                    logging.debug("goto refill paper")
                    self.PaperEmpty()
                    return
                if str(printerstate).find("02") > 0:
                    logging.debug("goto refill paper")
                    self.PaperEmpty()
                    return
                else:
                    logging.debug("Printer error: unbekannt")
    
            # Send the picture to the printer
            conn.printFile(printername[0], self.cardfilename, "Photo Booth", {})
    
            # short wait
            time.sleep(5)
    
            stop = 0
            TIMEOUT = 60
    
            # Wait until the job finishes
            while stop < TIMEOUT:
                printerstate = conn.getPrinterAttributes(printername[0], requested_attributes=["printer-state-message"])
    
                if str(printerstate).find("error:") > 0:
                    logging.debug(str(printerstate))
                    if str(printerstate).find("06") > 0:
                        logging.debug("goto refill ink")
                        self.InkEmpty()
                        return
                    if str(printerstate).find("03") > 0:
                        logging.debug("goto refill paper")
                        self.PaperEmpty()
                        return
                    if str(printerstate).find("02") > 0:
                        logging.debug("goto refill paper")
                        self.PaperEmpty()
                        return
                    else:
                        logging.debug("Printer error: unbekannt")
    
                if printerstate.get("printer-state-message") is "":
                    logging.debug("printer-state-message = /")
                    break
                stop += 1
                time.sleep(1)
    
        else:
            logging.debug("Print disabled")

        self.PrintDone()

    def on_exit_PrintCard(self):
        logging.debug("now on_exit_PrintCard")

    # show refill paper instructions
    def on_enter_RefillPaper(self):
        logging.debug("now on_enter_RefillPaper")
        self.overlayscreen_refillpaper = self.overlay_image(self.screen_change_paper, 0, 8)

    def on_exit_RefillPaper(self):
        logging.debug("now on_exit_RefillPaper")
        self.remove_overlay(self.overlayscreen_refillpaper)

    # show refill ink instructions
    def on_enter_RefillInk(self):
        logging.debug("now on_enter_RefillInk")
        self.overlayscreen_refillink = self.overlay_image(self.screen_change_ink, 0, 8)

    def on_exit_RefillInk(self):
        logging.debug("now on_exit_RefillInk")
        self.remove_overlay(self.overlayscreen_refillink)

    # restart the programm -> restart camera to prevent memory leak of image overlay function!
    def on_enter_Restart(self):
        logging.debug("now on_enter_Restart")
        logging.debug("restart Camera")

        self.camera.close()

        # Setup Camera
        try:
            self.camera = picamera.PiCamera()
        except:
            logging.CRITICAL("error initializing the camera - exiting")
            raise SystemExit

        self.camera.resolution = (self.photo_w, self.photo_h)
        self.camera.hflip = self.flip_screen_h
        self.camera.vflip = self.flip_screen_v
        self.startpreview()

        # load the Logo of the Photobooth and display it
        self.overlayscreen_logo = self.overlay_image_transparency(self.screen_logo, 0, 5)

        self.to_Start()

    # start the camera
    def startpreview(self):
        logging.debug("Start Camera preview")
        self.camera.start_preview(resolution=(self.screen_w, self.screen_h))
        # camera.color_effects = (128, 128)  # SW
        pass

    # stop the camera
    def stoppreview(self):
        logging.debug("Stop Camera Preview")
        self.camera.stop_preview()
        pass

    # create filename based on date and time
    def get_base_filename_for_images(self):
        logging.debug("Get BaseName for ImageFiles")
        # returns the filename base
        base_filename = self.photo_abs_file_path + str(datetime.now()).split('.')[0]
        base_filename = base_filename.replace(' ', '_')
        base_filename = base_filename.replace(':', '-')

        logging.debug(base_filename)
        return base_filename

    # remove screen overlay
    def remove_overlay(self, overlay_id):
        # If there is an overlay, remove it
        logging.debug("Remove Overlay")
        logging.debug(overlay_id)
        if overlay_id != -1:
            self.camera.remove_overlay(overlay_id)

    # overlay one image on screen
    def overlay_image(self, image_path, duration=0, layer=3):
        # Add an overlay (and time.sleep for an optional duration).
        # If time.sleep duration is not supplied, then overlay will need to be removed later.
        # This function returns an overlay id, which can be used to remove_overlay(id).

        if not os.path.exists(image_path):
            logging.debug("Overlay Image path not found!")
            logging.debug(image_path)
            return -1

        logging.debug("Overlay Image")
        # Load the arbitrarily sized image
        img = Image.open(image_path)
        # Create an image padded to the required size with
        # mode 'RGB'
        pad = Image.new('RGB', (
            ((img.size[0] + 31) // 32) * 32,
            ((img.size[1] + 15) // 16) * 16,
        ))
        # Paste the original image into the padded one
        pad.paste(img, (0, 0))

        # Add the overlay with the padded image as the source,
        # but the original image's dimensions
        try:
            o_id = self.camera.add_overlay(pad.tobytes(), size=img.size)
        except AttributeError:
            o_id = self.camera.add_overlay(pad.tostring(), size=img.size)  # Note: tostring() is deprecated in PIL v3.x

        o_id.layer = layer

        logging.debug("Overlay ID = " + str(o_id))

        del img
        del pad

        if duration > 0:
            time.sleep(duration)
            self.camera.remove_overlay(o_id)
            return -1  # '-1' indicates there is no overlay
        else:
            return o_id  # we have an overlay, and will need to remove it later

    # overlay omage with transparency
    def overlay_image_transparency(self, image_path, duration=0, layer=3):
        # Add an overlay (and time.sleep for an optional duration).
        # If time.sleep duration is not supplied, then overlay will need to be removed later.
        # This function returns an overlay id, which can be used to remove_overlay(id).

        if not os.path.exists(image_path):
            logging.debug("Overlay Image path not found!")
            logging.debug(image_path)
            return -1

        logging.debug("Overlay Transparency Image")
        logging.debug(image_path)
        # Load the arbitrarily sized image
        img = Image.open(image_path)
        # Create an image padded to the required size with
        # mode 'RGB'
        pad = Image.new('RGBA', (
            ((img.size[0] + 31) // 32) * 32,
            ((img.size[1] + 15) // 16) * 16,
        ))
        # Paste the original image into the padded one
        pad.paste(img, (0, 0), img)

        # Add the overlay with the padded image as the source,
        # but the original image's dimensions
        try:
            o_id = self.camera.add_overlay(pad.tobytes(), size=img.size)
        except AttributeError:
            o_id = self.camera.add_overlay(pad.tostring(), size=img.size)  # Note: tostring() is deprecated in PIL v3.x

        o_id.layer = layer

        logging.debug("Overlay ID = " + str(o_id))

        del img
        del pad

        if duration > 0:
            time.sleep(duration)
            self.camera.remove_overlay(o_id)
            return -1  # '-1' indicates there is no overlay
        else:
            return o_id  # we have an overlay, and will need to remove it later

    # get the usb drive mount point
    def GetMountpoint(self):
        logging.debug("Get USB Drive Mount Point")
        try:
            context = pyudev.Context()
            removable = [device for device in context.list_devices(subsystem='block', DEVTYPE='disk') if
                         device.attributes.asstring('removable') == "1"]

            partitions = [removable[0].device_node for removable[0] in
                          context.list_devices(subsystem='block', DEVTYPE='partition', parent=removable[0])]
            for p in psutil.disk_partitions():
                if p.device in partitions:
                    logging.debug("Mountpoint = " + p.mountpoint)
                    return p.mountpoint

        except:
            logging.debug("No Drive Found")
            return None

    # check if the printer is connected and turned on
    def CheckPrinter(self):
        logging.debug("CheckPrinter")

        if self.printPicsEnable == False:
            logging.debug("printing disabled")
            return True

        busses = usb.busses()
        for bus in busses:
            devices = bus.devices
            for dev in devices:
                if dev.idVendor == 1193:
                    logging.debug("Printer Found")
                    logging.debug("  idVendor: %d (0x%04x)" % (dev.idVendor, dev.idVendor))
                    logging.debug("  idProduct: %d (0x%04x)" % (dev.idProduct, dev.idProduct))
                    return True
        logging.debug("PrinterNotFound")
        return False


# Main Routine
def main():
    # start logging
    log_filename = str(datetime.now()).split('.')[0]
    log_filename = log_filename.replace(' ', '_')
    log_filename = log_filename.replace(':', '-')

    loggingfolder = REAL_PATH + "/Log/"

    if not os.path.exists(loggingfolder):
        os.mkdir(loggingfolder)

    # logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.DEBUG, filename=REAL_PATH+"/test.log")
    logging.basicConfig(format='%(asctime)s-%(module)s-%(funcName)s:%(lineno)d - %(message)s', level=logging.DEBUG,
                        filename=loggingfolder + log_filename + ".log")
    logging.info("info message")
    logging.debug("debug message")

    while True:

        logging.debug("Starting Photobooth")

        photobooth = Photobooth()

        while True:
            time.sleep(0.1)
            pass

        #photobooth.__del__()


if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        logging.debug("keyboard interrupt")

    except Exception as exception:
        logging.critical("unexpected error: " + str(exception))

    finally:
        logging.debug("logfile closed")
