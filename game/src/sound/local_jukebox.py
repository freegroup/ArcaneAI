import pygame
from pygame import mixer
import os
import threading

from sound.base import BaseJukebox
from logger_setup import logger

pygame.mixer.init()

class LocalJukebox(BaseJukebox):
    def __init__(self):
        # Dictionary to store channels with their loop status
        self.playing_channels = {}

    def play_sound(self, session, file_name, volume=100, loop=True, duration=2):
        """
        Play a sound from the given file path.
        :param file_path: Absolute path to the sound file (wav or mp3).
        :param loop: If True, play sound in an infinite loop; otherwise, play once.
        :return: PlayingSound object for controlling this sound.
        """
        if not file_name or len(file_name) == 0:
            return  # silently

        file_path = f"{session.map_dir}/{session.map_name}/soundfx/{file_name}"

        try:
            if not os.path.isabs(file_path):
                current_dir = os.path.dirname(os.path.abspath(__file__))
                file_path = os.path.join(current_dir, file_path)

            # Load the sound
            sound = mixer.Sound(file_path)

            # Find a free channel to play the sound
            channel = mixer.find_channel()
            if channel is None:
                raise RuntimeError("No free channel available to play sound")

            # Convert volume to a range between 0.0 and 1.0
            volume = max(0, min(volume, 100)) / 100.0
            channel.set_volume(volume)

            # Play the sound
            loops = -1 if loop else 0
            channel.play(sound, loops=loops)

            # Store the channel and its loop status in the dictionary
            self.playing_channels[channel] = {'loop': loop, 'timer': None}

            # Set a timer to stop the sound after the specified duration
            if duration > 0 and not loop:
                timer = threading.Timer(duration, self._stop_sound, args=[channel])
                self.playing_channels[channel]['timer'] = timer
                timer.start()

        except Exception as e:
            logger.error(f"Unable to play sound: '{file_path}', Error: {e}")


    def _stop_sound(self, channel):
        """Stop the specified channel and clean up. Callled from the timerThread only"""
        if channel in self.playing_channels:
            channel.stop()
            # Clear the channel from playing_channels
            del self.playing_channels[channel]


    def stop_all(self, session):
        """Stop all currently playing sounds."""
        for channel, info in list(self.playing_channels.items()):
            if channel.get_busy():
                channel.stop()
            if info['timer'] is not None:
                info['timer'].cancel()

        self.playing_channels.clear()


    def stop_ambient(self, session):
        """Stop only looping (ambient) sounds."""
        # Stop only channels that are looping
        for channel, info in list(self.playing_channels.items()):
            if info['loop'] and channel.get_busy():
                channel.stop()
                if info['timer'] is not None:
                    info['timer'].cancel()
                del self.playing_channels[channel]