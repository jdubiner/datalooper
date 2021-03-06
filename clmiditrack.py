import cltrack
from consts import *


class ClMidiTrack(cltrack.ClTrack):

    def __init__(self, parent, track, trackNum, song):
        super(ClMidiTrack, self).__init__(parent, track, trackNum, song)
        self.__parent = parent
        self.trackStore = []
        self.prevNotes = list()

    ### SCENARIOS ###
    # 1. No clip in memory, record starts recording and a new clip is made and selected
    # 2. Clip is already in memory and playing, meaning overdubbing will begin
    # 3. Clip is already in memory and stopped, meaning clip will play
    # 4. Clip is already in memory and recording, meaning clip will play
    #################
    def record(self, quantized):
        self.__parent.send_message("in record pressed")
        if self.clipSlot == -1:
            self.__parent.send_message("starting recording in new slot")
            # Scenario # 1
            self.getNewClipSlot()
            self.fireClip()
        elif self.clipSlot.has_clip:
            if self.clipSlot.clip.is_playing and not self.clipSlot.clip.is_recording:
                self.__parent.send_message("going to overdub")
                self.overdub()
                # Scenario 2
            elif not self.clipSlot.clip.is_playing and not self.clipSlot.clip.is_recording:
                self.__parent.send_message("playing clip from stopped state")
                # Scenario 3
                self.fireClip()
            elif self.clipSlot.clip.is_recording and not self.clipSlot.clip.is_overdubbing:
                # Scenario 4
                self.__parent.send_message("ending recording")
                self.fireClip()
            elif self.clipSlot.clip.is_overdubbing:
                self.endOverdub()
        elif self.clipSlot != -1 and not self.clipSlot.has_clip:
            self.__parent.send_message("recording new clip")
            # Scenario 5
            self.fireClip()

    def undo(self):
        self.undoOverdub()

    def clear(self):
        self.__parent.send_message("clear pressed")
        if self.clipSlot != -1 and self.clipSlot.has_clip:
            self.removeClip()
        self.__parent.send_message("Clearing Clip")

    def overdub(self):
        self.__parent.send_message("overdubbing")
        self.updateState(OVERDUB_STATE)
        self.__parent.session_record(True, self.track)
        if self.clipSlot.has_clip != -1:
            self.clipSlot.clip.select_all_notes()
            self.prevNotes.append(self.clipSlot.clip.get_selected_notes())
        self.song.session_record = 1

    def undoOverdub(self):
        if len(self.prevNotes) > 0 and self.clipSlot != -1 and self.clipSlot.has_clip:
            self.__parent.send_message("removing overdub")
            self.clipSlot.clip.select_all_notes()
            self.clipSlot.clip.replace_selected_notes(self.prevNotes[-1])
            del self.prevNotes[-1]

    def endOverdub(self):
        self.__parent.send_message("ending overdubbing")
        self.song.session_record = 0
        self.updateState(PLAYING_STATE)
        self.__parent.session_record(False, self.track)

    def new_clip(self):
        self.getNewClipSlot()


