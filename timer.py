#!/usr/bin/env python3
# timer.py
# /sable cantus/
# set a countdown timer in your terminal and play an alarm when done

import datetime
import os
import platform
import signal
import shutil
import subprocess
import sys
import threading
import time

alarm = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'watch_alarm.wav')

def get_sound_command():
    sound_player = {
        'Darwin': 'afplay',
        'Linux': 'aplay',
    }.get(platform.system())

    if not sound_player:
        return None, f"Sound playback is not configured for {platform.system()}."
    if not shutil.which(sound_player):
        return None, f"Sound player '{sound_player}' was not found."
    if not os.path.isfile(alarm):
        return None, f"Alarm sound file not found: {alarm}"
    return [sound_player, alarm], None


def print_boxed_message(message):
    """Prints a message inside a decorative ASCII box."""
    width = len(message) + 4
    print("┌" + "─" * (width - 2) + "┐")
    print(f"│ {message} │")
    print("└" + "─" * (width - 2) + "┘")

def get_boxed_input(prompt):
    """Displays a boxed prompt and returns user input."""
    print_boxed_message(prompt)
    return input(" > ")


def wait_for_keypress(prompt):
    """Wait for acknowledgment and restore terminal settings after raw input."""
    if not sys.stdin.isatty():
        input(prompt)
        return

    print(prompt, end='', flush=True)
    if os.name == 'nt':
        import msvcrt

        msvcrt.getch()
    else:
        import termios
        import tty

        file_descriptor = sys.stdin.fileno()
        previous_settings = termios.tcgetattr(file_descriptor)
        try:
            tty.setraw(file_descriptor)
            sys.stdin.read(1)
        finally:
            termios.tcsetattr(file_descriptor, termios.TCSADRAIN, previous_settings)
    print()


def is_muted():
    """Checks if the system audio is muted on macOS."""
    try:
        command_output = subprocess.check_output(['osascript', '-e', 'output muted of (get volume settings)'], text=True, stderr=subprocess.DEVNULL).strip()
        return command_output == 'true'
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def exit_on_termination(signum, _frame):
    raise SystemExit(128 + signum)


# Clear the screen first
subprocess.run(['clear'], check=True)

# Now, check for mute status and display the warning if needed.
mute_warning_active = is_muted()
if mute_warning_active:
    print("WARNING: Your system audio is muted. You may not hear the alarm.")

sound_command, sound_issue = get_sound_command()
if sound_issue:
    print(sound_issue)
    while True:
        choice = input("Choose [s]kip sound and continue, or [q]uit: ").strip().lower()
        if choice == 's':
            sound_command = None
            break
        if choice == 'q':
            sys.exit(0)
        print("Please enter 's' to continue without sound or 'q' to quit.")

if len(sys.argv) > 1 and sys.argv[1] == 'test':
    message = "testing"
    later = datetime.datetime.now() + datetime.timedelta(seconds=5)
    print_boxed_message("Running a 5-second test")
else:
    if len(sys.argv) > 1:
        reminder = int(sys.argv[1])
        # message = "your reminder"
        message = sys.argv[2] if len(sys.argv) > 2 else "your reminder"
    else:
        message = get_boxed_input("What should I remind you about?")
        reminder = get_boxed_input("In how many minutes?")

    pluralSingular = "minute" if int(reminder) == 1 else "minutes"
    print_boxed_message(f"Okay, I'll remind you in {reminder} {pluralSingular}")
    later = datetime.datetime.now() + datetime.timedelta(minutes=int(reminder))

spinner = ['|', '/', '-', '\\']
while datetime.datetime.now() < later:
    for s in spinner:
        remaining = later - datetime.datetime.now()
        if remaining.total_seconds() < 0:
            break
        secs = int(remaining.total_seconds())
        mins, secs = divmod(secs, 60)
        time_str = f" {mins:02d}:{secs:02d}"
        print(f" {s} {time_str}", end='\r')
        time.sleep(0.1)

stop_flashing = threading.Event()

def flash_screen(stop_event):
    try:
        while not stop_event.is_set():
            sys.stdout.write("\x1b[?5h") # Invert colors
            sys.stdout.flush()
            time.sleep(0.5)
            if stop_event.is_set(): break
            sys.stdout.write("\x1b[?5l") # Revert colors
            sys.stdout.flush()
            time.sleep(0.5)
    finally:
        sys.stdout.write("\x1b[?5l") # Ensure colors are reverted
        sys.stdout.flush()

# Clear the line with the spinner before showing the final message
print(" " * 20, end='\r')
print('\a')

alarmPlay = None
flash_thread = None
termination_signals = [signal.SIGTERM]
if hasattr(signal, 'SIGHUP'):
    termination_signals.append(signal.SIGHUP)
previous_signal_handlers = {}

try:
    for signum in termination_signals:
        previous_signal_handlers[signum] = signal.signal(signum, exit_on_termination)

    if sound_command:
        try:
            alarmPlay = subprocess.Popen(sound_command)
        except OSError as error:
            print(f"Could not start alarm sound: {error}", file=sys.stderr)

    flash_thread = threading.Thread(target=flash_screen, args=(stop_flashing,))
    flash_thread.start()

    print_boxed_message(f"Timer complete: {message}")
    wait_for_keypress('Press any key to acknowledge:')
finally:
    stop_flashing.set()
    try:
        if alarmPlay:
            alarmPlay.kill()
            alarmPlay.wait()
    finally:
        try:
            if flash_thread and flash_thread.ident is not None:
                flash_thread.join()
        finally:
            for signum, previous_handler in previous_signal_handlers.items():
                signal.signal(signum, previous_handler)
