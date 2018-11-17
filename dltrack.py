from consts import *
from time import time
import Live
from track import Track

class DlTrack(Track):
    """ Class handling looper track from DataLooper """

    def __init__(self, parent, track, device, trackNum, song):
        super(DlTrack, self).__init__(parent, track, trackNum, song)
        self.tempo_control = -1
        self.device = device
        self.state = device.parameters[STATE]
        self.rectime = 0
        self.ignore_stop = False
        self.req_record = True
        self.nextQuantize = -1
        self.__parent = parent
        self.quantizeTicks = -1
        self.quantization = -1
        self._notification_timer = -1
        self.lastState = CLEAR_STATE
        self.updateState(self.lastState)
        self.track.add_arm_listener(self.set_arm)

    def set_arm(self):
        if super(DlTrack, self).set_arm():
            if self.track.arm:
                self.updateState(CLEAR_STATE)
            else:
                self.updateState(DISARMED_STATE)

    def _on_looper_param_changed(self):
        if self.lastState == CLEAR_STATE and self.state.value == STOP_STATE:
            return
        elif not self.new_session_mode:
            self.send_message("Looper param changed: " + str(self.state.value))
            self.updateState(int(self.state.value))

    def send_message(self, message):
        self.__parent.send_message(message)


    def request_control(self, control):
        self.send_message("Requesting control: " + str(control))
        self.send_sysex(self.trackNum, REQUEST_CONTROL_COMMAND, control)

    def record(self):
        self.__parent.send_message(
            "Looper " + str(self.trackNum) + " state: " + str(self.device.parameters[STATE].value) + " rec pressed")
        if self.new_session_mode:
            if self.lastState == RECORDING_STATE:
                self.calculateBPM(time() - self.rectime)
                self.updateState(PLAYING_STATE)
                self.__parent.new_session(0,0)
            elif self.lastState == CLEAR_STATE:
                self.updateState(RECORDING_STATE)
                self.rectime = time()
        else:
            if not self.state.value_has_listener(self._on_looper_param_changed):
                self.state.add_value_listener(self._on_looper_param_changed)
            self.request_control(RECORD_CONTROL)

    def play(self):
        if self.lastState == STOP_STATE:
            self.request_control(RECORD_CONTROL)
            self.updateState(PLAYING_STATE)

    def stop(self):
        self.__parent.send_message(
            "Looper " + str(self.trackNum) + " state: " + str(self.device.parameters[1].value) + " stop pressed")
        if self.lastState == RECORDING_STATE:
            self.request_control(CLEAR_CONTROL)
            self.updateState(CLEAR_STATE)
            self.ignore_stop = True
        else:
            self.request_control(STOP_CONTROL)
        # todo clean this up, follow tempo
        #self.device.parameters[TEMPO_CONTROL].value = NO_SONG_CONTROL

    def toggle_playback(self):
        if self.lastState == STOP_STATE:
            self.request_control(RECORD_CONTROL)
        elif self.lastState == PLAYING_STATE:
            self.request_control(STOP_CONTROL)

    def undo(self):
        self.request_control(UNDO_CONTROL)
        self.__parent.send_message(
            "Looper " + str(self.trackNum) + " state: " + str(self.device.parameters[1].value) + " undo pressed")

    def clear(self):
        self.request_control(CLEAR_CONTROL)
        self.__parent.send_message(
            "Looper " + str(self.trackNum) + " state: " + str(self.device.parameters[1].value) + " clear pressed")
        self.updateState(CLEAR_STATE)

    def calculateBPM(self, loop_length):
        recmin = loop_length / 60
        bpm4 = 4 / recmin
        bpm8 = 8 / recmin
        bpm16 = 16 / recmin
        bpms = [bpm4, bpm8, bpm16]
        bpm = min(bpms, key=lambda x: abs(x - 100))
        self.send_message("bpm: " + str(bpm))
        self.__parent.set_bpm(bpm)

    def toggle_new_session_mode(self, new_session_mode):
        self.new_session_mode = new_session_mode
        if new_session_mode:
            self.quantization = self.device.parameters[QUANTIZATION].value
            self.tempo_control = self.device.parameters[TEMPO_CONTROL].value
            self.device.parameters[QUANTIZATION].value = NO_QUANTIZATION
            self.device.parameters[TEMPO_CONTROL].value = NO_TEMPO_CONTROL
        else:
            self.device.parameters[QUANTIZATION].value = self.quantization
            self.device.parameters[TEMPO_CONTROL].value = self.tempo_control
