import random

from pynars.Narsese import Term, parser
from pynars.NARS.DataStructures.MC.ChannelMC import ChannelMC


class SampleChannel4(ChannelMC):

    def __init__(self, num_slot, num_event, num_anticipation, num_operation, num_prediction, memory, ID):
        super(SampleChannel4, self).__init__(num_slot, num_event, num_anticipation, num_operation, num_prediction,
                                             memory, ID)
        self.operations = []

    def execute(self, term: Term):
        pass

    def information_gathering(self):
        ret = []
        if random.randint(0, 10) > 5:
            ret.append(parser.parse("<Robin --> Bird>."))
        else:
            ret.append(parser.parse("<Bird --> Animal>."))

        return ret
