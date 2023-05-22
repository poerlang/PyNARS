import numpy as np

from pynars.GUI.Ui_Form import escape
from pynars.NARS.DataStructures.MC import AnticipationMC, InputBufferMC
from pynars.Narsese import Task, Budget, Term, Judgement


# the priority value of events
def p_value(t: Task):
    return t.budget.priority * t.truth.f / t.term.complexity + np.random.rand() / 20


class SlotMC:
    """
    Each slot shall contain 3 parts:
    1) events, including input events and generated compounds;
    2) anticipations, events (including compounds) expected;
    3) to-do operations, these operations will be executed AT THE END of each cycle.
    """

    def __init__(self, num_event, num_anticipation, num_operation):
        self.num_event = num_event
        self.num_anticipation = num_anticipation
        self.num_operation = num_operation

        self.events = np.array([])
        self.anticipations = {}  # anticipations need no priorities, so a dictionary is enough, compared with a 3-tuple
        self.operations = []

        self.candidate = None  # a better name is "spatial-temporal candidate", but this name is too long
        self.spatial_candidate = None

    def update_events(self, t: Task):
        """
        Update a single event in the current time slot.
        Updating has two meanings:
        1) if there are no task with the same term, just add it;
        2) if there is a task with the same term, REPLACE the old one with the new one.
        """
        word = t.term.word
        # delete if existed
        if len(self.events) != 0:
            self.events = np.delete(self.events, np.where(self.events[:, 0] == word), axis=0).reshape((-1, 3))
        # then just add
        if len(self.events) == 0:
            self.events = np.array([(word, t, p_value(t))])
        else:
            self.events = np.append(self.events, [(word, t, p_value(t))], 0)
        # delete if overwhelmed
        # NO NEED TO SORT the PQ after each updating, you may do it when there are no further updates
        if len(self.events) > self.num_event:
            self.events = np.delete(self.events, np.where(self.events[:, 2] == self.events[:, 2].min()),
                                    axis=0).reshape((-1, 3))

    def update_anticipations(self, a: AnticipationMC):
        """
        There might be duplicate anticipations. All are used for revision.
        When the space for anticipations is full, no further anticipations will be accepted.
        """
        if len(self.anticipations) < self.num_anticipation:
            word = a.t.term.word
            if word in self.anticipations and p_value(a.t) > p_value(self.anticipations[word].t):
                self.anticipations.update({word: a})
            else:
                self.anticipations.update({word: a})

    def update_operations(self, term: Term):
        if len(self.operations) < self.num_operation:
            (Judgement(term), Budget(0.9, 0.9, 0.5))

    def check_anticipation(self, buffer: InputBufferMC, mode_unexpected = False):
        """
        Unexpected event:= not an anticipation
        Satisfied anticipation will be revised in to an event, and so we can recognize these events that are not
        anticipations, which is called UNEXPECTED.
        We might need to check these anticipations several time, but we don't need to check unexpected events often,
        so we have this "mode_unexpected" as an option.
        """
        events_updates = []  # satisfied anticipations will be used for revision, [:Task]
        events_updates_unexpected = []  # unexpected events will be boosted, if needed

        for each_event in self.events:
            if each_event[0] in self.anticipations:
                events_updates.append(self.anticipations[each_event[0]].satisfied(buffer, each_event[1]))
            elif mode_unexpected:
                task = Task(each_event[1].sentence,
                            Budget(min(0.99, each_event[1].budget.priority * 0.9), each_event[1].budget.durability,
                                   min(0.99, each_event[1].budget.quality * 0.9)))
                events_updates_unexpected.append(task)

        for each_event in events_updates:
            self.update_events(each_event)
        if mode_unexpected:
            for each_event_unexpected in events_updates_unexpected:
                self.update_events(each_event_unexpected)

        # unsatisfied anticipations will be handled in InputBufferMC.py

    def content(self):
        A = "<p style=\"text-align: center\"> <hr> </hr>"
        E = "<p style=\"text-align: center\"> <hr> </hr>"
        O = "<p style=\"text-align: center\"> <hr> </hr>"
        for each in self.anticipations:
            A += "<font color='red'>" + str(
                format(self.anticipations[each].t.truth.f, ".3f")) + "</font> | <font color='blue'>" + str(
                format(self.anticipations[each].t.truth.c, ".3f")) + "</font> <br> <b>" + escape(
                self.anticipations[each].t.term.word) + "</b> <br> <font color='green'>" + str(
                format(self.anticipations[each].t.budget.priority, ".3f")) + " | " + str(
                format(self.anticipations[each].t.budget.durability, ".3f")) + " | " + str(
                format(self.anticipations[each].t.budget.quality, ".3f")) + "</font> <hr> </hr>"
        for each in self.events:
            E += "<font color='red'>" + str(format(each[1].truth.f, ".3f")) + "</font> | <font color='blue'>" + str(
                format(each[1].truth.c, ".3f")) + "</font> <br> <b>" + escape(
                each[1].term.word) + "</b> <br> <font color='green'>" + str(
                format(each[1].budget.priority, ".3f")) + " | " + str(
                format(each[1].budget.durability, ".3f")) + " | " + str(
                format(each[1].budget.quality, ".3f")) + "</font> <hr> </hr>"
        for each in self.operations:
            O += "<font color='red'>" + str(format(each.truth.f, ".3f")) + "</font> | <font color='blue'>" + str(
                format(each.truth.c, ".3f")) + "</font> <br> <b>" + escape(
                each.term.word) + "</b> <br> <font color='green'>" + str(
                format(each.budget.priority, ".3f")) + " | " + str(
                format(each.budget.durability, ".3f")) + " | " + str(
                format(each.budget.quality, ".3f")) + "</font> <hr> </hr>"
        return [A, E, O]
