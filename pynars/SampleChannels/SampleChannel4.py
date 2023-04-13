import random

from pynars.Narsese import Term, parser
from pynars.NARS.DataStructures.MC.ChannelMC import ChannelMC


class SampleChannel4(ChannelMC):
    """
    This channel will repeat one pattern with some random characters.
    One pattern will be like [$X|$Y].
    $X has 4 digits, and there are only two possibilities: [A, B, C, D] or [X, B, C, Y].
    $Y has 2 digits, which are completely random.
    One example is, [A, B, C, D, H, H, X, B, C, Y, J, J, X, B, C, Y, K, K, ...]
    Currently, no noise is considered.

    NARS is required to predict the next digit at each time. The best is that a 50% acc is achieved.
    """

    def __init__(self, num_slot, num_event, num_anticipation, num_operation, num_prediction, memory, ID):
        super(SampleChannel4, self).__init__(num_slot, num_event, num_anticipation, num_operation, num_prediction,
                                             memory, ID)
        self.operations = []
        self.mode = 0
        self.count = 2
        self.history = ""

    def execute(self, term: Term):
        pass

    def information_gathering(self):
        ret = []
        if self.mode == 0:
            if self.history == "":
                ret.append(parser.parse("A."))
                self.history = "A"
            elif self.history == "A":
                ret.append(parser.parse("B."))
                self.history = "B"
            elif self.history == "B":
                ret.append(parser.parse("C."))
                self.history = "C"
            elif self.history == "C":
                ret.append(parser.parse("D."))
                self.history = "D"
            elif self.history == "D" and self.count == 2:
                ret.append(parser.parse(chr(random.randint(65, 90)) + "."))
                self.count -= 1
            elif self.history == "D" and self.count == 1:
                ret.append(parser.parse(chr(random.randint(65, 90)) + "."))
                self.count -= 1
            elif self.history == "D" and self.count == 0:
                if random.random() > 0.5:
                    self.mode = 1
                    ret.append(parser.parse("X."))
                    self.history = "X"
                    self.count = 2
                else:
                    self.mode = 0
                    ret.append(parser.parse("A."))
                    self.history = "A"
                    self.count = 2
        elif self.mode == 1:
            if self.history == "":
                ret.append(parser.parse("X."))
                self.history = "X"
            elif self.history == "X":
                ret.append(parser.parse("B."))
                self.history = "B"
            elif self.history == "B":
                ret.append(parser.parse("C."))
                self.history = "C"
            elif self.history == "C":
                ret.append(parser.parse("Y."))
                self.history = "Y"
            elif self.history == "Y" and self.count == 2:
                ret.append(parser.parse(chr(random.randint(65, 90)) + "."))
                self.count -= 1
            elif self.history == "Y" and self.count == 1:
                ret.append(parser.parse(chr(random.randint(65, 90)) + "."))
                self.count -= 1
            elif self.history == "Y" and self.count == 0:
                if random.random() > 0.5:
                    self.mode = 1
                    ret.append(parser.parse("X."))
                    self.history = "X"
                    self.count = 2
                else:
                    self.mode = 0
                    ret.append(parser.parse("A."))
                    self.history = "A"
                    self.count = 2

        return ret
