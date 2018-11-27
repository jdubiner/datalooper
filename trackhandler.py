# Embedded file name: /Users/versonator/Jenkins/live/output/mac_64_static/Release/python-bundle/MIDI Remote Scripts/_Axiom/Encoders.py
from _Generic.Devices import *
from claudiotrack import ClAudioTrack
from clmiditrack import ClMidiTrack
from consts import *
from datalooper.cltrack import ClTrack
from dltrack import DlTrack
import Live


class TrackHandler:
    """ Class handling looper & clip tracks """

    def __init__(self, parent, song):
        self.__parent = parent
        self.song = song
        self.tracks = []
        self.new_session_mode = False
        self.metro = -1
        self.trackStore = []
        self.taps = 0
        self.new_scene = False
        self.stopAll = False
        self.bpm = self.song.tempo
        self.timerCounter = 0
        self.duplicates = []
        self.timer = Live.Base.Timer(callback=self.execute_tempo_change, interval=1, repeat=True)

    def disconnect(self):
        self.__parent.disconnect()

    def clear_tracks(self):
        for track in self.tracks:
            track.remove_track()
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

    #if there are more that one tracks with same delimiter, check if one of them specifies LED control. Mark LED inactive on the alternate track
    def send_midi(self, midi):
        self.__parent.send_midi(midi)

    def send_message(self, message):
        self.__parent.send_message(message)

    def get_track(self, instance, looper_num):
        req_track = instance * 3 + looper_num
        tracks = []
        for track in self.tracks:
            if track.trackNum == req_track:
                tracks.append(track)
        return tracks

    def record(self, instance = 0, looper_num = 0, looper = 0):
        req_track = instance * 3 + looper_num
        if self.stopAll:
            self.song.metronome = self.metro
            self.jump_to_next_bar(False)
            self.stopAll = False
            for track in self.tracks:
                if isinstance(track, looper) and track.trackNum == req_track:
                    track.record(False)
        else:
            for track in self.tracks:
                self.send_message(track)
                if isinstance(track, looper) and track.trackNum == req_track:
                    track.record(True)

    def stop(self, instance=0, looper_num=0):
        self.send_message("stop")
        for track in self.get_track(instance, looper_num):
            track.stop(True)

    def undo(self, instance=0, looper_num=0):
        for track in self.get_track(instance, looper_num):
            track.undo()
        self.send_message("undo")

    def clear(self, instance=0, looper_num=0):
        for track in self.get_track(instance, looper_num):
            track.clear()
        self.send_message("clear")

    def clear_all(self, instance=0, looper_num=0):
        if not self.new_session_mode:
            if not self.check_uniform_state_cl([CLEAR_STATE]):
                self.new_scene = True
            for track in self.tracks:
                if isinstance(track, ClTrack):
                    track.getNewClipSlot()
                    track.stop(False)
                else:
                    track.clear()
            self.new_scene = False
        self.send_message("clear all")

    def toggle_start_stop_all(self, instance=0, looper_num=0):
        if not self.new_session_mode and not self.check_uniform_state([CLEAR_STATE]):
            if self.check_uniform_state([STOP_STATE, CLEAR_STATE]):
                self.jump_to_next_bar(True)
                self.song.metronome = self.metro
                self.metro = -1
                self.stopAll = False
                for track in self.tracks:
                    track.play(False)
            else:
                self.metro = self.song.metronome
                self.stopAll = True
                self.song.metronome = 0
                for track in self.tracks:
                    if track.lastState == PLAYING_STATE:
                        track.stop(False)

    def check_uniform_state(self, state):
        for track in self.tracks:
            self.send_message("track " + str(track.trackNum) + " State:" + str(track.lastState))
            if track.lastState not in state:
                return False
        return True

    def check_uniform_state_cl(self, state):
        for track in self.tracks:
            self.send_message("track " + str(track.trackNum) + " State:" + str(track.lastState))
            if isinstance(track, ClTrack) and track.lastState not in state:
                return False
        return True

    def mute_all(self, instance=0, looper_num=0):
        if not self.new_session_mode:
            for track in self.tracks:
                if track.track.mute == 1:
                    track.track.mute = 0
                else:
                    track.track.mute = 1
            self.send_message("mute all")

    def new_session(self, instance=0, looper_num=0):
        self.send_message("New session")
        self.new_session_mode = not self.new_session_mode
        self.toggle_new_session()

    def exit_new_session(self, instance=0, looper_num=0):
        if self.new_session_mode:
            self.new_session_mode = False
            self.toggle_new_session()

    def toggle_new_session(self):
        self.stopAll = False
        if self.new_session_mode:
            self.send_sysex(0, 4, 1)
            if self.metro  == -1:
                self.metro = self.song.metronome
            self.song.metronome = 0
            self.taps = 0
        else:
            self.send_sysex(0, 4, 0)
            self.song.metronome = self.metro
        for track in self.tracks:
            track.toggle_new_session_mode(self.new_session_mode)

    def send_sysex(self, looper, control, data):
        self.__parent.send_sysex(looper, control, data)

    def set_bpm(self, bpm):
        self.__parent.set_bpm(bpm)

    def enter_config(self, instance=0, looper_num=0):
        self.send_message("Config toggled")
        self.send_sysex(0, 5, 0)

    def record_looper(self, instance=0, looper_num=0):
        self.send_message("in record looper")
        self.record(instance, looper_num, DlTrack)

    def record_clip(self, instance=0, looper_num=0):
        self.send_message("in record clip")
        if not self.new_session_mode:
            self.record(instance, looper_num, ClTrack)

    def find_last_slot(self):
        index = []
        for cl_track in self.tracks:
            if isinstance(cl_track, ClTrack):
                index.append(cl_track.find_last_slot())
        return max(index)

    def jump_to_next_bar(self, changeBPM):
        rec_flag = self.song.record_mode
        time = int(self.song.current_song_time) + (self.song.signature_denominator - (
                    int(self.song.current_song_time) % self.song.signature_denominator))
        self.send_message("current time:" + str(self.song.current_song_time) + "time: " + str(time))
        self.bpm = self.song.tempo
        self.song.current_song_time = time
        self.song.record_mode = rec_flag
        if changeBPM:
            self.timerCounter = 0
            self.timer.start()

    def execute_tempo_change(self):
        #kills timer after 50ms just in case it wants to run forever for some reason
        self.timerCounter += 1
        if self.song.tempo != self.bpm:
            self.song.tempo = self.bpm
            self.send_message("timer counter: " + str(self.timerCounter))
            self.timer.stop()
        elif self.timerCounter > 50:
            self.timer.stop()
            self.send_message("timer counter: " + str(self.timerCounter))

    def exit_config(self, instance=0, looper_num=0):
        self.send_message("exiting config")
        self.exit_new_session(instance, looper_num)

    def change_instance(self, instance=0, looper_num=0):
        self.send_message("changing instance to " + str(instance))
        i = 0
        while i < NUM_TRACKS:
            self.send_sysex(instance * NUM_TRACKS + i, CHANGE_STATE_COMMAND, CLEAR_STATE)
            i += 1
        new_tracks = [loop_track for loop_track in self.tracks if
                      instance * 3 <= loop_track.trackNum < instance * 3 + NUM_TRACKS]
        for loop_track in new_tracks:
            if isinstance(loop_track, ClTrack):
                for alt_track in self.tracks:
                    if isinstance(alt_track, ClTrack) and alt_track not in new_tracks and alt_track.track.current_input_routing == loop_track.track.current_input_routing:
                        alt_track.track.arm = 0
                loop_track.track.arm = 1
            self.send_sysex(loop_track.trackNum, CHANGE_STATE_COMMAND, loop_track.lastState)

    def bank(self, instance=0, looper_num=0):
        self.__parent.send_program_change(looper_num)

    def bank_if_clear(self, instance=0, looper_num=0):
        for track in self.get_track(instance, looper_num):
            if track.lastState != CLEAR_STATE:
                return
        self.bank(instance, looper_num)

    def new_clip(self, instance=0, looper_num=0):
        for track in self.get_track(instance, looper_num):
            track.new_clip()

    def session_record(self, overdubbing, curTrack):
        if overdubbing:
            for track in self.tracks:
                track.track.remove_arm_listener(track.set_arm)
            for track in self.song.tracks:
                if track.name != curTrack.name and track.can_be_armed:
                    self.trackStore.append(TempTrack(track.name, track.arm, track.current_monitoring_state))
                    if track.arm == 1:
                        track.arm = 0
                        if track.current_monitoring_state == 1 and track.playing_slot_index == -1:
                            track.current_monitoring_state = 0
        else:
            for track in self.song.tracks:
                if track.name != curTrack.name and track.can_be_armed:
                    match = next((trackS for trackS in self.trackStore if track.name == trackS.name), None)
                    if match is not None:
                        track.current_monitoring_state = match.current_monitoring_state
                        track.arm = match.arm
            for track in self.tracks:
                track.track.add_arm_listener(track.set_arm)

    def tap_tempo(self, looper=0, instance=0):
        if self.new_session_mode:
            self.song.tap_tempo()
            if self.taps >= 3:
                self.song.metronome = self.metro
            self.taps += 1

class TempTrack(object):
    def __init__(self, name, arm, current_monitoring_state):
        self.name = name
        self.arm = arm
        self.current_monitoring_state = current_monitoring_state
