from abc import abstractmethod

from pynars.NARS.DataStructures.MC.EventBufferMC import EventBufferMC
from pynars.Narsese import Term


class ChannelMC:

    def __init__(self, num_slot, num_event, num_anticipation, num_operation, num_prediction, memory, ID):
        self.ID = ID
        self.num_slot = num_slot * 2 + 1
        self.operations = []
        self.event_buffer = EventBufferMC(num_slot, num_event, num_anticipation, num_operation, num_prediction, memory)

    @abstractmethod
    def execute(self, term: Term):
        pass

    @abstractmethod
    def information_gathering(self):
        return None

    def step(self):
        new_contents = self.information_gathering()
        task_forward = self.event_buffer.step(new_contents, "SC2")
        return task_forward
