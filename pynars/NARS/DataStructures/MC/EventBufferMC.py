import numpy as np

from pynars.NARS.DataStructures import Memory
from pynars.NARS.DataStructures.MC.InputBufferMC import InputBufferMC
from pynars.NARS.DataStructures.MC.SlotMC import SlotMC


class EventBufferMC(InputBufferMC):

    def __init__(self, num_slot, num_event, num_anticipation, num_operation, num_prediction, memory: Memory):
        super(EventBufferMC, self).__init__(num_slot, num_event, num_anticipation, num_operation, num_prediction,
                                            memory)

    def operation_processing_default(self):
        """
        A default processing of operations. "By default" means that an operation is used as an event, and they are
        combined used in compound generation.

        And the operation is not used specially in prediction generation as "procedural knowledge".
        """
        self.slots[self.present].events = np.append(self.slots[self.present].events,
                                                    self.slots[self.present - 1].operations)

    def step(self, new_content, origin = ""):
        """
        Event buffer can get at most one new content each time, and so there are no "concurrent compound generations"
        in definition. But this will change if "default operation processing" is considered.
        """
        # remove the oldest slot and create a new one
        self.slots = self.slots[1:]
        self.slots.append(SlotMC(self.num_event, self.num_anticipation, self.num_operation))

        self.operation_processing_default()  # default operation processing
        self.concurrent_compound_generation(new_content, origin)  # 1st step
        self.historical_compound_generation(origin)  # 1st step
        self.local_evaluation()  # 2nd step
        self.memory_based_evaluations()  # 3rd step
        task_forward = self.prediction_generation()  # 4th step

        return task_forward
