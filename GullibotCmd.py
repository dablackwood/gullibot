"""
Gullibot Team:
    Nidhi Sekhar - Computational Design
    Mailing Wu - Mechanical Engineering
    Evan Dvorak - Mechanical Engineering
    David Blackwood - Computational Design
    Carnegie Mellon, Principles of Human-Robot Interaction, Fall 2014
    
"""

# General imports here.
import time
import os

class GullibotSession(object):
    ### Initialization ###
    def __init__(self, lcdActive=True, audioActive=False, tiltServoActive=True,
                 panServoActive=True, ledActive=True):
        (self.lcdActive, self.audioActive) = (lcdActive, audioActive)
        self.tiltServoActive = tiltServoActive 
        self.panServoActive = panServoActive
        self.ledActive = ledActive
        self.initCharDisplay()
#         self.initAudio()
        self.initServoBasic()       # assign channels for tilt & pan servos
        if tiltServoActive:
            self.resetServoPosition("tilt", 170)
        if panServoActive:
            self.resetServoPosition("pan", 180) 
        self.initLED()              # assign channel for indicator LED
        self.initAdvice()           # read-in all supplied text files
        self.initOtherMessages()
            
    def initCharDisplay(self):
        if self.lcdActive:
            import lcddriver
            self.lcd = lcddriver.lcd()
        else:
            self.lcd = None
        self.lcdLineLength = 20
        self.lcdNumLines = 4
    
#     def initAudio(self):
#         if self.audioActive:
#             import pygame
#             pygame.mixer.init()
#             BUFFER = 3072
#             FREQ, SIZE, CHAN = pygame.mixer.get_init()
#             pygame.mixer.init(FREQ, SIZE, CHAN, BUFFER)
#         else: pass

    def initServoBasic(self):
        self.servoChannels = {}
        GullibotSession.initChannel(self.servoChannels, "tilt", 0)
        GullibotSession.initChannel(self.servoChannels, "pan",  1)
        self.servoPositions = { "tilt":170, "pan":180 } # The starting position.
        self.maxServoStep = {"tilt":1, "pan":0.4}
        self.tiltLimits = (145, 200)
    
    def resetServoPosition(self, mode, position):
        servoChannel = self.servoChannels.get(mode, None)
        if (servoChannel != None):
#             self.smoothServo(mode, position)
            self.setServo(servoChannel, position)
            self.servoPositions[mode] = position
    
    @staticmethod
    def initChannel(group, mode, channel):
        # Assigns servoblaster channel to a string in given "group" dict.
        group[mode] = channel
    
    def initLED(self):
        self.ledChannels = {}
        if self.ledActive:
            # Note: Indicator LED may me hardwired to on!
            GullibotSession.initChannel(self.ledChannels, "indicator", 3)
            GullibotSession.initChannel(self.ledChannels, "scan", 4)
            ledChannel = self.ledChannels.get("scan", None)
            self.setServo(ledChannel, 0)
        self.scanLedIsOn = False
        # LEDs use servoblaster, too.
    
    def initAdvice(self):
        # Verifies advice files and copies into a list.
        # to do.... Initialize audio files.
        advicePath = "script/"
        self.getAdviceFiles(advicePath)
        self.setAdvice()
    
    def initOtherMessages(self):
        # All text files besides advice.
        scriptPath = "script/"
        scriptTypes = ["greeting", "prescan", "scanning", "evaluating", "closing", "adios"]
        messages = []
        for i in xrange(len(scriptTypes)):
            rawText = self.loadSingleTextFile(scriptPath, scriptTypes[i])
            messages.append(self.lcdParser(rawText))
        self.greeting =     messages[0]
        self.prescan =      messages[1]
        self.scanning =     messages[2]
        self.evaluating =   messages[3]
        self.closing =      messages[4]
        self.adios =        messages[5]
            
    def loadSingleTextFile(self, scriptPath, prefix):
        # Takes string and opens 1st file whose filename starts with prefix.
        (lineLength, numLines) = (self.lcdLineLength, self.lcdNumLines)
        allPaths = sorted(os.listdir(scriptPath))
        for i in xrange(len(allPaths)):
            fileName = allPaths[i]
            if fileName.startswith(prefix) and fileName.endswith(".txt"):
                fullPath = scriptPath + fileName
                with open(fullPath, 'r') as data:
                    text = data.read()
                data.closed
                print fullPath,
                if (len(text) <= (lineLength * numLines)): # 1st level check.
                    print "OK!"
                    return text
                else:
                    print "Too long: %d characters." % len(text)
        
    def getAdviceFiles(self, advicePath):
        self.advicePaths = {}
        (lineLength, numLines) = (self.lcdLineLength, self.lcdNumLines)
        allPaths = sorted(os.listdir(advicePath))
        for i in xrange(len(allPaths)):
            fileName = allPaths[i]
            if fileName.startswith("advice") and fileName.endswith(".txt"):
                fullPath = advicePath + fileName
                with open(fullPath, 'r') as data:
                    text = data.read()
                data.closed
                print fullPath,
                if (len(text) <= (lineLength * numLines)): # 1st level check.
                    self.advicePaths[i] = fullPath
                    print "OK!"
                else:
                    print "Too long: %d characters." % len(text)
    
    def setAdvice(self):
        self.allAdvice = {}
        for key in self.advicePaths:
            path = self.advicePaths[key]
            with open(path, 'r') as file:
                text = file.read()
            file.closed
            self.allAdvice[key] = text

    def displayStatus(self):
        for servo in self.servoPositions:
            print "  %s servo at position %d." % (servo, self.servoPositions[servo])
        print "Status OK."
    
    ### Higher-Level Controls ###
    def run(self):
        self.initControls()
        self.mainLoop()
    
    def initControls(self):
        print "Controller for Gullibot."
        print "These commands are available:"
        if self.tiltServoActive:
            self.validCmds = [ "pan", "tilt", "say", "servo", "light" ]
        else:
            self.validCmds = [ "pan", "tilt", "say", "light" ]
        print "   ".join(self.validCmds)
 
    def mainLoop(self):
        # Contains the main loop that waits for feedback from console.
        self.displayStatus()
        while True:
            print
            cmd = raw_input('>')
            # Parse, then send parsed cmd to be executed.
            parsed = GullibotSession.parseCmd(cmd)
            if (parsed != []) and (parsed[0] in self.validCmds):
                print "Executing command..."
                self.executeCmd(parsed)
                print "Done."
            else:
                print "Invalid command."
            self.displayStatus()

    def runFullScript(self):
        # Contains pre-scripted interaction.
        self.displayStatus()
        # Operator aligns robot to participant.
        print "Enter 'pan XXX' to point to direction XXX."
        print "Enter 'next' to proceed."
        self.panControl()
        # Intro.
        self.writeToCharDisplay(self.greeting)
        self.nod(blink=True)
        print "Just gave greeting."
        self.waitForOperator()
        self.writeToCharDisplay(self.prescan)
        print "Announced intent to scan..."
        self.waitForOperator()
        # Scanning motion.
        self.writeToCharDisplay(self.scanning)
        print "Running scan."
        self.runScan()
        # "Evaluate" posture.
        self.writeToCharDisplay(self.evaluating)
        print "Evaluating posture. Waiting 2 seconds."
        time.sleep(2)
        self.waitForOperator()
        # Advice.
        self.nod(blink=True)
        self.say(GullibotSession.parseCmd("say 6"))
        print "Gave advice. Waiting 5 seconds."
        time.sleep(5)
        self.waitForOperator()
        # Exit.
        self.writeToCharDisplay(self.closing)
        time.sleep(3)
        self.nod(blink=False)
        self.writeToCharDisplay(self.adios)
        print "SCRIPT COMPLETE!"
        print "Go pick-up the robot!"
        self.promptRestart()
    
    def promptRestart(self):
        while True:
            print
            willRestart = raw_input("Start script from beginning? [y,n]")
            if (willRestart.lower() in ["y", "n"]): break
        if (willRestart == "y"):
            self.resetServoPosition("tilt", 165)
            self.resetServoPosition("pan", 180)
            self.runFullScript()
        else: 
            print "Session closed."
        
    @staticmethod
    def parseCmd(cmd):
        # Takes the raw input of the command and breaks it into a list of strings.
        # Format is [ "verb", "modifier" ], where verb is the function called, and
        # "modifier" can be the amount to move, which advice to give, etc.
        return cmd.lower().split() # For now.

    def executeCmd(self, parsed):
        # Takes parsed string command and calls the relevant function.
#         print "Command received:", parsed
        if (len(parsed) == 2) and (parsed[0] == "pan"):
            print "Rotating body"
            # do the rotation
            self.panOrTilt(parsed, "pan")
        elif (len(parsed) == 2) and (parsed[0] == "tilt"):
            print "Tilting head"
            # do the tilt
            self.panOrTilt(parsed, "tilt")
        elif (len(parsed) == 2) and (parsed[0] == "say"):
            # display/voice words
            self.say(parsed)
        elif (parsed[0] == "servo") and (parsed[1] == "scan"):
            print "Calling both servos!!!"
            # rotate right / left
            self.runScan()
        elif (len(parsed) == 2) and (parsed[0] == "light"):
            print "Controlling LEDs"
            self.light(parsed)
        else:
            print "Invalid command."
    
    def waitForOperator(self):
        # Used for pauses in script.
        while True:
            entry = raw_input("Press ENTER to continue.")
            break
        channel = self.servoChannels.get("tilt", None)
        if (channel != None):
            self.setServo(channel, self.servoPositions["tilt"]) # Keeps robot from nodding off.
    
    def panControl(self):
        # Condensed version of initControls & mainloop.
        self.validCmds = [ "pan", "next" ]
        while True:
            cmd = raw_input('>')
            # Parse, then send parsed cmd to be executed.
            if (cmd == "next"):
                break
            elif (cmd[:3] == "pan"):
                parsed = GullibotSession.parseCmd(cmd)
                if (parsed != []) and (parsed[0] in self.validCmds):
                    print "Executing command..."
                    self.executeCmd(parsed)
                    print "Done."
            else:
                print "Invalid command."
            self.displayStatus()
    
    def panOrTilt(self, parsed, mode):
        # Takes parsed cmd & string mode: "pan" or "tilt"
        servoChannel = self.servoChannels.get(mode, None)
        position = self.servoPositions.get(mode, None)
        target = int(round(float(parsed[1])))
        if ((servoChannel != None) and (position != None)):
            # Move servo at channel
            # Need to check for target within range!
            print ("Rotating %s servo from %i to %i position." % 
                   (mode, position, target))
            if (((mode == "pan") and (self.panServoActive)) or
                ((mode == "tilt") and (self.tiltServoActive))):
                self.smoothServo(mode, target)
                self.servoPositions[mode] = target
        elif (position == None):
            print mode + "servo position not assigned."
        else:
            print mode + "servo channel not assigned."

    def smoothServo(self, mode, target, overrideSpeed=None, blink=False):
        # Breaks servo motion up into multiple steps.
        # If an overrideSpeed is given, use that as the servo step.
        (tiltMin, tiltMax) = self.tiltLimits
        if ((mode == "tilt") and ((target < tiltMin) or (target > tiltMax))): return
        channel = self.servoChannels.get(mode, None)
        position = self.servoPositions.get(mode, None)
        blinkTime =  0.1  # seconds
        servoSleep = 0.01 # seconds
        timingRatio = int(round(blinkTime / servoSleep)) # used with blinkCount
        if ((channel != None) and (position != None)):
            if (overrideSpeed == None):
                if   (mode == "tilt"): maxStepSize = self.maxServoStep["tilt"]
                elif (mode == "pan"):  maxStepSize = self.maxServoStep["pan"]
            else:
                maxStepSize = overrideSpeed
            sign = +1 if (target > position) else -1
            blinkCount = 0
            while (abs(target - position) > maxStepSize):
                if (blinkCount == timingRatio):
                    if blink: self.switchLED()
                    blinkCount = 0
                thisTarget = position + sign * maxStepSize
                self.setServo(channel, thisTarget)
                time.sleep(servoSleep)
                position = thisTarget
                self.servoPositions[mode] = position
                blinkCount += 1
            self.setServo(channel, target) # Final bump to target.
            self.servoPositions[mode] = target
    
    def switchLED(self):
        # Used for blinking during scan motion.
        ledChannel = self.ledChannels.get("scan", None)
        if (self.scanLedIsOn):
            self.setServo(ledChannel, 0)
        else:
            self.setServo(ledChannel, 220)
        self.scanLedIsOn = not self.scanLedIsOn
    
    def runScan(self):
        # Scripted behavior for running posture scan.
        tiltPos = self.servoPositions.get("tilt", None)
        panPos = self.servoPositions.get("pan", None)
        if ((tiltPos != None) and (panPos != None)):
            for loop in xrange(2):
                self.smoothServo("tilt", tiltPos-10, blink=True)
                self.smoothServo("pan",  panPos-7,   overrideSpeed=0.2, blink=True)
                self.smoothServo("pan",  panPos+7,   overrideSpeed=0.2, blink=True)
                self.smoothServo("pan",  panPos,     overrideSpeed=0.2, blink=True)
                self.smoothServo("tilt", tiltPos,    overrideSpeed=0.4, blink=True)
                time.sleep(0.5)
                self.smoothServo("tilt", tiltPos-15, overrideSpeed=0.2, blink=True)
                time.sleep(0.5)
                self.smoothServo("tilt", tiltPos,    overrideSpeed=0.4, blink=True)
    
    def nod(self, blink=False):
        # Scripted behavior for small nod motion.
        tiltPos = self.servoPositions.get("tilt", None) # Starting position
        (tiltMin, tiltMax) = self.tiltLimits
        if (tiltPos != None):
            for loop in xrange(1):
                self.smoothServo("tilt", max(tiltPos-5, tiltMin),
                                 overrideSpeed=0.6, blink=blink)
                self.smoothServo("tilt", tiltPos, overrideSpeed=0.4, blink=blink)
        
    def say(self, parsed):
        # Takes parsed cmd and initiates robot activity.
        adviceIndex = int(parsed[1])
        advice = self.allAdvice.get(adviceIndex, None)
        # call to character display / text-to-speech
        if (advice != None):
            print "Delivering text/speech:"
            lcdText = self.lcdParser(advice)
            self.writeToCharDisplay(lcdText)
            if (self.audioActive != False):
                self.audioSay(adviceIndex)
            else:
                print "If audio were active, file %d would play." % adviceIndex
        else: print "Invalid number for 'say' command."
    
    def writeToCharDisplay(self, text):
        # Takes list of length 4, each item is a string of length 20 chars.
        lcd = self.lcd
        for index in xrange(len(text)):
            line = text[index]
            if (self.lcdActive): lcd.lcd_display_string(line, index + 1)
            else: print line # Allows testing without character display.
    
    def audioSay(self, adviceIndex):
        try:
           initMixer()
           if (adviceIndex == 1): filename = "script/audioFake00.wav"
           #elif (adviceIndex == 2): filename = "needhug.wav" 
           playmusic(filename)
        except KeyboardInterrupt:	# to stop playing, press "ctrl-c"
           stopmusic()
           print "\nPlay Stopped by user"
        except Exception:
           print "unknown error"
    
    def playMusic(self, soundfile):
        pygame.init()
        pygame.mixer.init()
        clock = pygame.time.Clock()
        pygame.mixer.music.load(soundfile)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            clock.tick(1000)
    
    def light(self, parsed):
        # Takes parsed cmd and turns LEDs on and off.
        switch = parsed[1] # "on" or "off" or "test"
        ledChannel = self.ledChannels.get("indicator", None) # Only single LED
        scanLedCh = self.ledChannels.get("scan", None)
        if ((ledChannel != None) and (switch == "on")):
            # Turn LED on
            print "Setting LED to ON."
            self.indicatorOn()
        elif ((ledChannel != None) and (switch == "off")):
            # Turn LED off
            print "Setting LED to OFF."
            self.indicatorOff()
        elif ((ledChannel != None) and (switch == "test") and (scanLedCh != None)):
            # Test two LEDs
            print "Testing two LEDs."
            self.testLEDs()
        elif (ledChannel == None):
            print "LED channel not assigned."
            return
        else:
            print "Light command either 'on' or 'off'."
            return
    
    def indicatorOn(self, onTime=2):
        # From LEDcontrol.py time in seconds
        ledChannel1 = self.ledChannels.get("scan", None)
        self.setServo(ledChannel1, 220)
    
    def indicatorOff(self):
        ledChannel = self.ledChannels.get("scan", None)
        self.setServo(ledChannel, 0)
    
    def testLEDs(self):
        ledChannel1 = self.ledChannels.get("indicator", None)
        ledChannel2 = self.ledChannels.get("scan", None)
        self.indicatorOn()
        # Use 1st version (full on/off blink)
        for blink in xrange(20):
            self.setServo(ledChannel2, 0)
            time.sleep(0.1)
            self.setServo(ledChannel2, 220)
            time.sleep(0.1)
        self.indicatorOff()
        time.sleep(0.5)
        for blink in xrange(20):
            self.setServo(ledChannel2, 100)
            time.sleep(0.1)
            self.setServo(ledChannel1, 220)
            self.setServo(ledChannel2, 220)
            time.sleep(0.1)
        self.setServo(ledChannel1, 0)
        self.setServo(ledChannel2, 0)
    
    def blinkLED(self):
        ledChannel = self.ledChannels.get("scan", None)
        for blink in xrange(10):
            self.setServo(ledChannel, 0)
            time.sleep(0.1)
            self.setServo(ledChannel, 220)
            time.sleep(0.1)
        self.setServo(ledChannel, 0)
    
    def lcdParser(self, text):
        # Takes (possibly multiline) string. Returns list of strings.
        lines = []
        text = text.replace("\n", " ")
        words = text.split(" ")
        for line in xrange(self.lcdNumLines):
            thisLine = []
            lineLength = 0
            while True:
                if len(words) > 0: wordLength = len(words[0])
                else: break
                if (lineLength + wordLength) <= self.lcdLineLength:
                    # ... accounting for final space.
                    thisLine.append(words.pop(0))
                    lineLength += (wordLength + 1)
                else: break
            lineString = " ".join(thisLine).strip().ljust(20)
            lines.append(lineString)
        return lines

    def setServo(self, servoChannel, position):
        # Source: http://raspberrypi-aa.github.io/session2/pwm-servo.html
        servoStr ="%u=%u\n" % (servoChannel, position)
        with open("/dev/servoblaster", "wb") as f:
            f.write(bytearray(servoStr, 'UTF-8'))

    def testLCDParser(self):
        print "\nTesting lcdParser()...",
        text1 = "aaaa bbbb cccc dddd eeee ffff."
        text2 = """\
    aaaaaaaaaa bbbbbbbbbb cccccccccc
    dddddddddd eeeeeeeeee."""
        texts = [text1, text2]
        result1 = [ "aaaa bbbb cccc dddd ",
                    "eeee ffff.          ",
                    "                    ",
                    "                    " ]
        result2 = [ "aaaaaaaaaa          ",
                    "bbbbbbbbbb          ",
                    "cccccccccc          ",
                    "dddddddddd          " ]
        results = [result1, result2]
        for i in xrange(2):
            assert( self.lcdParser(texts[i]) == results[i] )
        print "OK!"

    def testAll(self):
        self.testLCDParser()

def runScript():
    session = GullibotSession(lcdActive=True, audioActive=False,
                              tiltServoActive=True, panServoActive=True,
                              ledActive=True)
    session.testAll()
    session.runFullScript()

def runControl():
    (lcdActive, audioActive, tiltServoActive, panServoActive, ledActive) = runSetup()
    print (lcdActive, audioActive, tiltServoActive, panServoActive, ledActive)
    audioActive = False # Did not work with PWM servo control.
    session = GullibotSession(lcdActive, audioActive, tiltServoActive,
                              panServoActive, ledActive)
    session.testAll()
    session.run()

def runSetup():
    while True:
        lcdYN = raw_input("Is the character display connected? [y/n]  ")
        if (lcdYN.lower() in ["y", "n"]): break
    audioYN = "n" # Did not work with PWM servo control.
    while True:
        tiltYN = raw_input("Is the tilt servo connected? [y/n]  ")
        if (tiltYN.lower() in ["y", "n"]): break
    while True:
        panYN = raw_input("Is the pan servo connected? [y/n]  ")
        if (panYN.lower() in ["y", "n"]): break
    while True:
        ledYN = raw_input("Is the LED panel connected? [y/n]  ")
        if (ledYN.lower() in ["y", "n"]): break
    results = []
    for yn in [ lcdYN, audioYN, tiltYN, panYN, ledYN]:
        if (yn.lower() == "y"): results.append(True)
        else: results.append(False)
    return list(results)

def runDevelop():
    session = GullibotSession(lcdActive=False, audioActive=False,
                              tiltServoActive=False, panServoActive=False,
                              ledActive=False)
    session.testAll()
    session.run()

def promptMode():
    modeInstructions = """\
Select mode:
'script'  - Pre-defined interaction sequence (with some input).
'control' - Operator selects all commands.
'develop' - Test code without robot."""
    print modeInstructions
    while True:
        userInput = raw_input(">")
        if (userInput in ["script", "control", "test", "develop"]): break
    if (userInput == "script"): runScript()
    elif (userInput == "control"): runControl()
    else: runDevelop()

if __name__ == "__main__":
    promptMode()
   