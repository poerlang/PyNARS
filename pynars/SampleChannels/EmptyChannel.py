import random

from pynars.Narsese import Term, parser
from pynars.NARS.DataStructures.MC.ChannelMC import ChannelMC


class EmptyChannel(ChannelMC):
    """
    An empty channel, it will perceive and act nothing. If so, the only input is from the overall buffer to the
    memory, with possible temporal and spatial compounding.
    """

    def __init__(self, num_slot, num_event, num_anticipation, num_operation, num_prediction, memory, ID):
        super(EmptyChannel, self).__init__(num_slot, num_event, num_anticipation, num_operation, num_prediction,
                                           memory, ID)
        self.operations = []
        self.mode = 0
        self.count = 2
        self.history = ""

    def execute(self, term: Term):
        pass

    def information_gathering(self):
        ret = []
        return ret
