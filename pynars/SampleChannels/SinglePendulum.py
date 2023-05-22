from pynars.NARS.DataStructures.MC.ChannelMC import ChannelMC
from pynars.Narsese import Term, parser


class SinglePendulum(ChannelMC):

    def __init__(self, num_slot, num_event, num_anticipation, num_operation, num_prediction, memory, ID):
        super(SinglePendulum, self).__init__(num_slot, num_event, num_anticipation, num_operation, num_prediction,
                                             memory, ID)
        self.operations = []
        self.sequence = "LLLLLRRRRRLLLRRRLLRR".split()
        self.pos = 0

    def execute(self, term: Term):
        pass

    def information_gathering(self):
        # a low default budget
        ret = parser.parse("$0.2;0.1;0.1$ <(*,{SELF}," + self.sequence[self.pos] + ")-->SEE>.")
        if self.pos != len(self.sequence) - 1:
            self.pos += 1
        else:
            self.pos = 0

        return ret
