from copy import deepcopy

import numpy as np

from pynars.GUI.Ui_Form import escape
from pynars.NAL.Functions import Stamp_merge, Budget_merge, Truth_induction, Truth_deduction
from pynars.NARS.DataStructures import Memory
import pynars.NARS.DataStructures.MC.AnticipationMC as AnticipationMC
import pynars.NARS.DataStructures.MC.SlotMC as SlotMC
from pynars.NARS.DataStructures.MC.UncannyTerms import UncannyTerms
from pynars.Narsese import Compound, Task, Judgement, Interval, Statement, Copula


# the priority value of predictions (predictive implications)
def p_value(t: Task):
    return t.budget.summary * t.truth.e / t.term.complexity ** 2


def UI_better_content(task: Task):
    """
    A function to help generate UI output.
    Make it not just plain texts.
    Since each buffer (event buffer, internal buffer, global buffer) will have an independent UI page.
    """
    budget = "$" + str(task.budget.priority)[:4] + ";" + str(task.budget.durability)[:4] + ";" + str(
        task.budget.quality)[:4] + "$ | "
    word = "".join(task.sentence.word.split(" ")) + "\n"
    end = "=" * 41 + "\n"
    word.replace("-->", "->")
    word.replace("==>", "=>")
    if task.truth is not None:
        truth = "% " + str(task.truth.f)[:4] + ";" + str(task.truth.c)[:4] + "%\n"
        return [budget + truth, word, end]
    else:
        return [budget + "\n", word, end]


class InputBufferMC(object):
    """
    The super class of all input buffers (event buffer, internal buffer, global buffer).
    """

    def __init__(self, num_slot, num_event, num_anticipation, num_operation, num_prediction, memory: Memory):
        self.num_slot = num_slot * 2 + 1
        self.present = num_slot

        self.num_event = num_event
        self.num_anticipation = num_anticipation
        self.num_operation = num_operation
        self.num_prediction = num_prediction

        self.memory = memory
        """
        Though this is called uncanny "term", actually this is a dictionary of strings (to save some time).
        The key is the name (word) of the term, and the value is the 
        """
        self.uncanny_terms = UncannyTerms(100, 50)  # TODO, make them as arguments
        self.prediction_table = []
        self.prediction_penalty = {}
        self.slots = [SlotMC(num_event, num_anticipation, num_operation) for _ in range(self.num_slot)]

    def update_prediction(self, p: Task):
        self.prediction_penalty.update({p.term.word: self.present})
        for i in range(len(self.prediction_table)):  # delete if existed
            if self.prediction_table[i].term == p.term:
                if self.prediction_table[i].term.word in self.prediction_penalty:
                    self.prediction_penalty.pop(self.prediction_table[i].term.word)
                del self.prediction_table[i]
                break
        P = p_value(p)
        added = False
        # large to small
        for i in range(len(self.prediction_table)):
            if P > p_value(self.prediction_table[i]):
                self.prediction_table = self.prediction_table[:i] + [p] + self.prediction_table[i:]
                added = True
                break
        if not added:  # smallest
            self.prediction_table = self.prediction_table + [p]
        if len(self.prediction_table) > self.num_prediction:
            if self.prediction_table[-1].term.word in self.prediction_penalty:
                self.prediction_penalty.pop(self.prediction_table[-1].term.word)
            self.prediction_table = self.prediction_table[:-1]
        # if a prediction is missed for self.present slots, it will be dropped

    def combination(self, lst, start, num, tmp, cpds):
        """
        Compound utility function.
        """
        if num == 0:
            cpds.append(deepcopy(tmp))
            return
        elif len(lst) - start < num:
            return
        else:
            tmp.append(lst[start])
            self.combination(lst, start + 1, num - 1, tmp, cpds)
            self.combination(lst[:-1], start + 1, num, tmp, cpds)

    def concurrent_compound_generation(self, new_contents, origin = ""):
        """
        Spatial pattern generation.

        Each buffer will have a compound generation process, and this process is exactly the same. Though in some
        buffers, a part of the process is skipped due to blank inputs.

        For example, in event buffers, usually this step will be skipped since there are only one event at each time.
        """
        if new_contents is None:
            return
        for new_content in new_contents:
            self.slots[self.present].update_events(new_content)
        # check atomic anticipations
        self.slots[self.present].check_anticipation(self)

        # concurrent compounds generation
        compounds = []
        for i in range(len(self.slots[self.present].events)):
            self.combination(self.slots[self.present].events[:, 1], 0, i + 1, [], compounds)
        for each_compound in compounds:
            if len(each_compound) > 1:
                # term generation
                each_compound_term = [each.term for each in each_compound]
                term = Compound.ParallelEvents(*each_compound_term)
                # truth, using truth-induction function (TODO, may subject to change)
                truth = each_compound[0].truth
                for each in each_compound[1:]:
                    truth = Truth_induction(truth, each.truth)
                # stamp, using stamp-merge function (TODO, may subject to change)
                stamp = each_compound[0].stamp
                for each in each_compound[1:]:
                    stamp = Stamp_merge(stamp, each.stamp)
                # budget, using budget-merge function (TODO, may subject to change)
                budget = each_compound[0].budget
                for each in each_compound[1:]:
                    budget = Budget_merge(budget, each.budget)
                # sentence composition
                sentence = Judgement(term, stamp, truth)
                # task generation
                task = Task(sentence, budget)
                self.slots[self.present].update_events(task)
            else:
                self.slots[self.present].update_events(each_compound[0])
        # check concurrent compound anticipations
        self.slots[self.present].check_anticipation(self)
        # set the spatial pattern
        if len(self.slots[self.present].events) != 0:
            self.slots[self.present].spatial_candidate = self.slots[self.present].events[
                np.where(self.slots[self.present].events[:, 2] == self.slots[self.present].events[:, 2].max())[
                    0].item()][1]

    def historical_compound_generation(self, origin = ""):
        """
        Temporal (continuing the previous spatial) pattern generation.

        Previously, this is achieved by a DP-like process, but currently it is achieved by exhaustion.

        It happens among all the present concurrent compound and all "previous candidates", like finding a sub-string.
        Note that one current event may not be included.
        """
        if self.slots[self.present].events is None:
            return
        for i in range(len(self.slots[self.present].events)):
            """
            tmp_list is a list of previous spatial candidates
            we are going to find the sub string of this "string"
            there might be "None" in tmp_list
            select previous candidates
            """
            tmp_list = [self.slots[i].spatial_candidate for i in range(self.present)] + [
                self.slots[self.present].events[i][1]]
            for j in range(1, 2 ** (self.present + 1)):  # enumeration, actually this is a process finding sub-strings
                # a binary coding is used to find the sub-string
                j_binary_str = list(("{:0" + str(self.present + 1) + "b}").format(j))
                j_binary_boolean = [False if each == "0" else True for each in j_binary_str]
                cpd = []
                for k, each in enumerate(j_binary_boolean):
                    if not each:
                        cpd.append(1)
                    elif tmp_list[k] is not None:
                        cpd.append(tmp_list[k])
                    else:
                        cpd.append(1)
                # for example
                # tmp_list: [None, None, A, None, None, B, C]
                # i_binary_boolean: [False, False, True, True, True, True, False]
                # cpd: [1, 1, A, 1, 1, B, 1], remove the 1's at the beginning and ending
                while True:
                    if len(cpd) != 0 and cpd[0] == 1:
                        cpd = cpd[1:]
                    else:
                        break
                # cpd: [A, 1, 1, B, 1], or []
                if len(cpd) != 0:
                    while True:
                        if cpd[-1] == 1:
                            cpd = cpd[:-1]
                        else:
                            break
                # cpd: [A, 1, 1, B], cpd is a list of tasks, merge adjacent intervals next
                cpd_term = []
                if len(cpd) != 0:
                    interval = 0
                    for k, each in enumerate(cpd):
                        if each != 1:
                            if interval != 0:
                                cpd_term.append(Interval(interval))
                                interval = 0
                            cpd_term.append(each.term)  # each isType Task
                        else:
                            interval += 1
                # cpd_term: [A.term, Interval(2), B.term] or [] TODO: ugly, but work :\

                if len(cpd_term) != 0:
                    term = Compound.SequentialEvents(*cpd_term)
                    truth = cpd[0].truth
                    stamp = cpd[0].stamp
                    budget = cpd[0].budget
                    for each in cpd[1:]:
                        if each != 1:
                            # truth, using truth-induction function (TODO, may subject to change)
                            truth = Truth_induction(truth, each.truth)
                            # stamp, using stamp-merge function (TODO, may subject to change)
                            stamp = Stamp_merge(stamp, each.stamp)
                            # budget, using budget-merge function (TODO, may subject to change)
                            budget = Budget_merge(budget, each.budget)
                    # sentence composition
                    sentence = Judgement(term, stamp, truth)
                    # task generation
                    task = Task(sentence, budget)
                    self.slots[self.present].update_events(task)

            # checking historical events is moved to the end of local_evaluation

    def local_evaluation(self):

        # TODO, slow and ugly, but make sense
        tmp = []
        for each_prediction in self.prediction_table:
            if each_prediction.term.word in self.prediction_penalty:
                if self.prediction_penalty[each_prediction.term.word] != 0:
                    tmp.append(each_prediction)
                else:
                    self.prediction_penalty.pop(each_prediction.term.word)
        self.prediction_table = tmp

        # generate anticipation
        for each_prediction in self.prediction_table:

            # a subject is found first and then a search on all events
            # if a prediction can fire, it is good, but if it cannot often, it will be dropped

            # predictions may be like "(&/, A, +1) =/> B", the content of the subject will just be A
            # if it is "(&/, A, +1, B) =/> C", no need to change the subject

            interval = 0
            if isinstance(each_prediction.term.subject.terms[-1], Interval):
                subject = Compound.SequentialEvents(*each_prediction.term.subject.terms[:-1])  # condition
                interval = int(each_prediction.term.subject.terms[-1])
            else:
                subject = each_prediction.term.subject

            activated = False
            for each_event in self.slots[self.present].events:
                if subject.equal(each_event[1].term):
                    activated = True
                    self.prediction_penalty[each_prediction.term.word] = self.present
                    # term generation
                    term = each_prediction.term.predicate
                    # truth, using truth-deduction function (TODO, may subject to change)
                    truth = Truth_deduction(each_prediction.truth, each_event[1].truth)
                    # stamp, using stamp-merge function (TODO, may subject to change)
                    stamp = Stamp_merge(each_prediction.stamp, each_event[1].stamp)
                    # budget, using budget-merge function (TODO, may subject to change)
                    budget = Budget_merge(each_prediction.budget, each_event[1].budget)
                    # sentence composition
                    sentence = Judgement(term, stamp, truth)
                    # task generation
                    task = Task(sentence, budget)
                    # anticipation generation
                    anticipation = AnticipationMC(task, each_prediction)
                    if interval <= self.present:
                        self.slots[self.present + interval].update_anticipations(anticipation)

            if not activated:
                self.prediction_penalty[each_prediction.term.word] -= 1

        # check anticipations with un-expectation handling (non-anticipation events)
        self.slots[self.present].check_anticipation(self, mode_unexpected=True)

        """
        After the last round of anticipation checking in one cycle, we will find out the non-good predictions, 
        and so punishing themselves and the corresponding subject. Since if one prediction is not good, 
        we may think whether its precondition (subject) is not good. This will further generate a list of uncanny terms,
        and so their priority (NOT the priority in budget) will be decreased.
        
        Currently, it will be GREATLY decreased (divided by 2).
        """

        # unsatisfied anticipation handling
        for each_anticipation in self.slots[self.present].anticipations:
            if not self.slots[self.present].anticipations[each_anticipation].solved:
                # punish the predictions
                self.slots[self.present].anticipations[each_anticipation].unsatisfied(self)
                # punish the preconditions
                if isinstance(
                        self.slots[self.present].anticipations[each_anticipation].parent_prediction.term.subject.terms[
                            -1], Interval):
                    subject = Compound.SequentialEvents(
                        *self.slots[self.present].anticipations[each_anticipation].parent_prediction.term.subject.terms[
                         :-1])  # condition
                else:
                    subject = self.slots[self.present].anticipations[each_anticipation].parent_prediction.term.subject
                self.uncanny_terms.update_uncanny_terms(subject.word)

    def memory_based_evaluations(self):
        """
        Find whether a concept is already in the main memory. If so, merger the budget.
        """
        events_updates = []

        for each_event in self.slots[self.present].events:
            tmp = self.memory.concepts.take_by_key(each_event[1].term, remove=False)
            if tmp is not None:
                budget = Budget_merge(each_event[1].budget, tmp.budget)
                task = Task(each_event[1].sentence, budget)
                events_updates.append(task)
        for each_event in events_updates:
            self.slots[self.present].update_events(each_event)

        # find the highest concurrent compound, namely the candidate
        # before sorting, apply the effects of these uncanny term
        for i in range(len(self.slots[self.present].events)):
            A, B = self.uncanny_terms.check(self.slots[self.present].events[i][0])
            if A:
                self.slots[self.present].events[i][2] /= B

        # then sorting
        if len(self.slots[self.present].events) != 0:
            self.slots[self.present].events = self.slots[self.present].events[
                np.argsort(self.slots[self.present].events[:, 2])]
            self.slots[self.present].candidate = self.slots[self.present].events[-1][1]

    def prediction_generation(self):
        # subject =/> predict
        if self.slots[self.present].candidate is not None:
            predicate = self.slots[self.present].spatial_candidate.term
            for i in range(self.present):
                if self.slots[i].candidate:
                    # e.g., (E, +1) as the subject
                    subject = Compound.SequentialEvents(self.slots[i].spatial_candidate.term,
                                                        Interval(abs(self.present - i)))
                    copula = Copula.PredictiveImplication  # =/>
                    term = Statement(subject, copula, predicate)
                    # truth, using truth-induction function (TODO, may subject to change)
                    truth = Truth_induction(self.slots[i].candidate.truth,
                                            self.slots[self.present].candidate.truth)
                    # stamp, using stamp-merge function (TODO, may subject to change)
                    stamp = Stamp_merge(self.slots[i].candidate.stamp,
                                        self.slots[self.present].candidate.stamp)
                    # budget, using budget-merge function (TODO, may subject to change)
                    budget = Budget_merge(self.slots[i].candidate.budget,
                                          self.slots[self.present].candidate.budget)
                    # sentence composition
                    sentence = Judgement(term, stamp, truth)
                    # task generation
                    prediction = Task(sentence, budget)
                    self.update_prediction(prediction)
        return self.slots[self.present].candidate

    def reset(self):
        self.slots = [SlotMC(self.num_event, self.num_anticipation, self.num_operation) for _ in range(self.num_slot)]
        self.prediction_table = []

    def content(self):
        P = "<p style=\"text-align: center\"> <hr> </hr>"
        for each in self.prediction_table:
            P += "<font color='red'>" + str(
                format(each.truth.f, ".3f")) + "</font> | <font color='blue'>" + str(
                format(each.truth.c, ".3f")) + "</font> <br> <b>" + escape(
                each.term.word) + "</b> <br> <font color='green'>" + str(
                format(each.budget.priority, ".3f")) + " | " + str(
                format(each.budget.durability, ".3f")) + " | " + str(
                format(each.budget.quality, ".3f")) + "</font> <hr> </hr>"
        AEOs = []
        for each_slot in self.slots:
            AEOs.append(each_slot.content())
        return [AEOs, P]
