#!/usr/bin/env python3

# timer.py
# /sable cantus/
# set a countdown timer and play the buzzer

import datetime
import time
import subprocess
import os
import sys

# you may need the script to change directory
# to be in the same location as your wav file
# os.chdir('/your/path/here/')

# must run in the same directory as the wav file
alarm = ('watch_alarm.wav')

# was a time specified at the prompt?
# if it was, use that in minutes
if len(sys.argv) > 1:
    reminder = int(sys.argv[1])
    message = "your reminder"
else:
    message = input("reminder message: ")
    reminder = input("remind in X minutes: ")

os.system('clear')

# check for 1 minute or more
if int(reminder) == 1:
    pluralSingular = "minute"
else:
    pluralSingular = "minutes"

print("Okay, I'll remind you in", reminder, pluralSingular)

later = datetime.datetime.now() + datetime.timedelta(minutes = int(reminder))

while datetime.datetime.now() < later:
    print(' .', end='\r')
    time.sleep(0.5)
    print('  ', end='\r')
    time.sleep(0.5)

print('\a')

# sound the alarm
# for macOS
alarmPlay = subprocess.Popen(['afplay', 'watch_alarm.wav'])

# for ubuntu
# alarmPlay = subprocess.Popen(['aplay', 'watch_alarm.wav'])

# notify the user and give them a chance to kill the alarm
print("You're timer is complete: ", message)
input('any key to acknowledge')

# after clicking on input
alarmPlay.kill()
