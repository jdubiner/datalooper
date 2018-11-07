# Embedded file name: /Users/versonator/Jenkins/live/output/mac_64_static/Release/python-bundle/MIDI Remote Scripts/_Axiom/Encoders.py
from _Generic.Devices import *
from claudiotrack import ClAudioTrack
from clmiditrack import ClMidiTrack
from consts import *
from dltrack import DlTrack


class TrackHandler:
    """ Class handling looper & clip tracks """

    def __init__(self, parent, song):
        self.__parent = parent
        self.song = song
        self.tracks = []
        self.new_session_mode = False
        self.metro = self.song.metronome

    def disconnect(self):
        self.__parent.disconnect()

    def clear_tracks(self):
        self.tracks = []

    def append_tracks(self, track, trackNum, track_key):
        if track_key == DATALOOPER_KEY:
            # adds a listener to tracks detected as DataLoopers to rescan for looper when a devices is added
            if not track.devices_has_listener(self.__parent.scan_tracks):
                track.add_devices_listener(self.__parent.scan_tracks)
            # checks for devices
            if track.devices:
                for device in track.devices:
                    if device.name == "Looper":
                        self.send_message("adding looper track")
                        self.tracks.append(DlTrack(self, track, device, trackNum, self.song))
                    else:
                        self.send_message("Looper Device Does Not Exist on Track: " + track.name)
        elif track_key == CLIPLOOPER_KEY:
            if track.has_midi_input:
                self.send_message("adding clip midi track")
                self.tracks.append(ClMidiTrack(self, track, trackNum, self.song))
            elif track.has_audio_input:
                self.send_message("adding clip audio track")
                self.tracks.append(ClAudioTrack(self, track, trackNum, self.song))

    def send_midi(self, midi):
        self.__parent.send_midi(midi)

    def send_message(self, message):
        self.__parent.send_message(message)

    def get_track(self, instance, looper_num):
        req_track = instance * 3 + looper_num + 1
        tracks = []
        for track in self.tracks:
            self.send_message(str(req_track) + " :" + str(track.trackNum))
            if track.trackNum == req_track:
                tracks.append(track)
        return tracks

    def record(self, instance, looper_num):
        self.send_message("recording")
        for track in self.get_track(instance, looper_num):
            track.record()

    def stop(self, instance, looper_num):
        self.send_message("stop")
        for track in self.get_track(instance, looper_num):
            track.stop()

    def undo(self, instance, looper_num):
        for track in self.get_track(instance, looper_num):
            track.undo()
        self.send_message("undo")

    def clear(self, instance, looper_num):
        for track in self.get_track(instance, looper_num):
            track.clear()
        self.send_message("clear")

    def clear_all(self, instance, looper_num):
        if not self.new_session_mode:
            for track in self.tracks:
                track.clear()
            self.send_message("clear all")

    def stop_all(self, instance, looper_num):
        if not self.new_session_mode:
            for track in self.tracks:
                track.stop()
            self.send_message("stop all")

    def mute_all(self, instance, looper_num):
        for track in self.tracks:
            if track.track.mute == 1:
                track.track.mute = 0
            else:
                track.track.mute = 1
        self.send_message("mute all")

    def new_session(self, instance, looper_num):
        self.send_message("New session")
        self.new_session_mode = not self.new_session_mode
        self.toggle_new_session()

    def exit_new_session(self, instance, looper_num):
        if self.new_session_mode:
            self.new_session_mode = False
            self.toggle_new_session()

    def toggle_new_session(self):
        if self.new_session_mode:
            self.send_sysex(0, 4, 1)
            self.metro = self.song.metronome
            self.song.metronome = 0
        else:
            self.send_sysex(0, 4, 0)
            self.song.metronome = self.metro
        for track in self.tracks:
            track.toggle_new_session_mode(self.new_session_mode)

    def send_sysex(self, looper, control, data):
        self.__parent.send_sysex(looper, control, data)

    def set_bpm(self, bpm):
        self.__parent.set_bpm(bpm)

    def enter_config(self, instance, looper_num):
        self.send_message("Config toggled")
        self.send_sysex(0, 5, 0)

    def exit_config(self, instance, looper_num):
        pass