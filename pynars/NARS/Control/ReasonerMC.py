import time
from typing import List

import numpy as np
from matplotlib import pyplot as plt

from pynars import Config, Global
from pynars.GUI.Ui_Form import Ui_Form
from pynars.GUI.Ui_Form import escape
from ..DataStructures import Memory, Task, Concept
from ..DataStructures.MC.ChannelMC import ChannelMC
from ..DataStructures.MC.GlobalBufferMC import GlobalBufferMC
from ..DataStructures.MC.InternalBufferMC import InternalBufferMC
from ..DataStructures.MC.OutputBufferMC import OutputBufferMC
from ..InferenceEngine import GeneralEngine
from ...Narsese import parser
from ...SampleChannels.EmptyChannel import EmptyChannel


class ReasonerMC(Ui_Form):

    def __init__(self, n_memory, config = './config.json') -> None:
        super(ReasonerMC, self).__init__()
        Config.load(config)
        self.inference = GeneralEngine()
        self.previous_inference_result = []
        self.output_buffer = OutputBufferMC()
        self.memory = Memory(n_memory, output_buffer=self.output_buffer)
        # self.channels: List[ChannelMC] = [
        #     SampleChannel4(3, 5, 10, 10, 10, self.memory, "Channel_1"),
        # ]
        self.channels: List[ChannelMC] = [
            EmptyChannel(3, 5, 10, 10, 10, self.memory, "Channel_1"),
        ]
        self.internal_buffer = InternalBufferMC(3, 5, 10, 10, 10, self.memory, Mode304=True)
        self.global_buffer = GlobalBufferMC(3, 5, 10, 10, 10, self.memory, Mode304=True)
        for i, each_channel in enumerate(self.channels):
            self.IDC[each_channel.ID] = 2 + i
            self.output_buffer.register_channel(each_channel)
            self.IDs.append(each_channel.ID)
        self.num_channels = len(self.channels)
        self.num_slots = 3 * 2 + 1  # TODO, different channels may have different num_slots

        # self.questions = {"<ID1-->ID2>", "<ID1-->ID7>", "<ID2-->ID0>", "<ID3-->ID0>", "<ID4-->ID2>", "<ID4-->ID3>",
        #                   "<ID5-->ID8>", "<ID5-->ID9>", "<ID7-->ID0>", "<ID7-->ID3>", "<ID7-->ID4>", "<ID8-->ID3>",
        #                   "<ID9-->ID2>", "<ID9-->ID4>", "<ID9-->ID6>"}
        self.questions = {"<ID1-->ID0>", "<ID1-->ID4>", "<ID4-->ID0>"}
        self.new_questions = set()
        self.solved_questions = set()
        self.solved_new_questions = set()
        self.cycle_count = 1

    def input_lines(self, texts: List[str]):
        """
        collect the content in the input window; parse them into Narsese and process
        a task will be directly accept() by the main memory
        """
        for text in texts:
            if text:
                t = parser.parse(text)
                task_revised, goal_derived, answers_question, answer_quest = self.memory.accept(t)
                if answers_question is not None and len(answers_question) != 0:
                    if answers_question[0].term.word not in self.questions:
                        self.solved_new_questions.add(answers_question[0].term.word)
                    else:
                        self.solved_questions.add(answers_question[0].term.word)

    def reset(self):
        """
        Everything in the buffers should be cleared: 1) slots, 2) prediction table, 3) operation agenda.
        """
        self.output_buffer.reset()
        self.internal_buffer.reset()
        self.global_buffer.reset()
        for each in self.channels:
            each.event_buffer.reset()

    def cycles(self, n_cycle: int):
        for _ in range(n_cycle):
            self.cycle()

    def cycle(self):
        """
        Everything to do by NARS in a single working cycle
        """
        if self.cycle_count % 5 == 0:
            memory_visualization = []
            for each in self.memory.concepts.levels:
                for each_level in each:
                    memory_visualization.append(each_level.budget.priority)
            plt.figure()
            plt.ylim((0, 1))
            plt.grid()
            plt.plot(memory_visualization, marker="o")
            plt.show()
        # ==============================================================================================================

        # step 1, take out a task from the internal buffer, and put it into the global buffer
        task_from_internal_buffer = self.internal_buffer.step(self.previous_inference_result, "internal")
        self.previous_inference_result = []

        # step 2, Take out a task from each channel, and put it into the global buffer
        tasks_from_channels = []
        for i, each_channel in enumerate(self.channels):
            if not self.active_button[self.IDC[each_channel.ID]].isChecked():
                tasks_from_channels.append(each_channel.step())

        # step 3, execute the task from the internal buffer if (mentally) executable
        # only mental operations will be executed after the selection of the internal buffer
        # but here, we don't have mental operations yet TODO
        # so this function is currently skipped
        pass

        # step 4, merge the task from the internal buffer and the tasks from channels
        if not self.internal_buffer.Mode304:
            tasks_for_global_buffer = tasks_from_channels + [task_from_internal_buffer]
            tasks_for_global_buffer = list(filter(None, tasks_for_global_buffer))
        else:
            tasks_for_global_buffer = task_from_internal_buffer

        # step 5, feed these tasks to the global buffer and send the one from the global buffer to the main memory
        # this will let us know the "direct process" of processing "THIS" task
        if not self.global_buffer.Mode304:
            task_from_global_buffer = self.global_buffer.step(tasks_for_global_buffer)
            if task_from_global_buffer is not None:
                judgement_revised, goal_revised, answers_question, answers_quest = \
                    self.memory.accept(task_from_global_buffer)
                if goal_revised is not None:
                    exist = False
                    for i in range(len(self.output_buffer.active_goals)):
                        if self.output_buffer.active_goals[i][0].term.equal(goal_revised.term):
                            self.output_buffer.active_goals = self.output_buffer.active_goals[:i] + [
                                [goal_revised, "updated"]] + self.output_buffer.active_goals[i:]
                            exist = True
                            break
                    if not exist:
                        self.output_buffer.active_goals.append([goal_revised, "initialized"])
                if answers_question is not None and len(answers_question) != 0:
                    for each in answers_question:
                        exist = False
                        for i in range(len(self.output_buffer.active_questions)):
                            if self.output_buffer.active_questions[i][0].term.equal(each.term):
                                self.output_buffer.active_questions = self.output_buffer.active_questions[:i] + [
                                    [each, "updated"]] + self.output_buffer.active_questions[i:]
                                exist = True
                                break
                        if not exist:
                            self.output_buffer.active_questions.append([each, "initialized"])
            else:
                judgement_revised, goal_revised, answers_question, answers_quest = None, None, None, None
            if judgement_revised is not None:
                self.previous_inference_result.append(judgement_revised)
            if goal_revised is not None:
                self.previous_inference_result.append(goal_revised)
            if answers_question is not None:
                for answer in answers_question:
                    self.previous_inference_result.append(answer)
            if answers_quest is not None:
                pass  # TODO
        else:  # Mode304 is on
            tasks_from_global_buffer = self.global_buffer.step(tasks_for_global_buffer)
            for task_from_global_buffer in tasks_from_global_buffer:
                if task_from_global_buffer is not None:
                    if task_from_global_buffer.is_question:
                        if task_from_global_buffer.term.word not in self.questions:
                            self.new_questions.add(task_from_global_buffer.term.word)
                    judgement_revised, goal_revised, answers_question, answers_quest = \
                        self.memory.accept(task_from_global_buffer)
                    if answers_question is not None and len(answers_question) != 0:
                        if answers_question[0].term.word not in self.questions:
                            self.solved_new_questions.add(answers_question[0].term.word)
                        else:
                            self.solved_questions.add(answers_question[0].term.word)
                    if goal_revised is not None:
                        exist = False
                        for i in range(len(self.output_buffer.active_goals)):
                            if self.output_buffer.active_goals[i][0].term.equal(goal_revised.term):
                                self.output_buffer.active_goals = self.output_buffer.active_goals[:i] + [
                                    [goal_revised, "updated"]] + self.output_buffer.active_goals[i:]
                                exist = True
                                break
                        if not exist:
                            self.output_buffer.active_goals.append([goal_revised, "initialized"])
                    if answers_question is not None and len(answers_question) != 0:
                        for each in answers_question:
                            exist = False
                            for i in range(len(self.output_buffer.active_questions)):
                                if self.output_buffer.active_questions[i][0].term.equal(each.term):
                                    self.output_buffer.active_questions = self.output_buffer.active_questions[:i] + [
                                        [each, "updated"]] + self.output_buffer.active_questions[i:]
                                    exist = True
                                    break
                            if not exist:
                                self.output_buffer.active_questions.append([each, "initialized"])
                else:
                    judgement_revised, goal_revised, answers_question, answers_quest = None, None, None, None
                if judgement_revised is not None:
                    self.previous_inference_result.append(judgement_revised)
                if goal_revised is not None:
                    self.previous_inference_result.append(goal_revised)
                if answers_question is not None:
                    for answer in answers_question:
                        self.previous_inference_result.append(answer)
                if answers_quest is not None:
                    pass  # TODO

        # step 6, apply general inference step
        # This will include the tasks generated by processing "A NEW (different from the previous)" task.
        concept: Concept = self.memory.take(remove=True)
        tasks_derived: List[Task] = []
        if concept is not None:

            tasks_inference_derived = self.inference.step(concept)
            tasks_derived.extend(tasks_inference_derived)
            for each in tasks_derived:
                print(each.term)
                self.previous_inference_result.append(each)
                self.output_buffer.step(each)
            self.memory.put_back(concept)

        # handle the sense of time
        Global.time += 1

        for each in tasks_derived:
            if each.is_question:
                self.output_buffer.active_questions.append([each, "derived"])
            elif each.is_goal:
                self.output_buffer.active_goals.append([each, "derived"])

        # TODO: EXPERIMENT
        """
        Try to get the accuracy of predictions at each time slot. But currently this is only for one event buffer.
        """
        # ==============================================================================================================
        # self.tmp = []
        # acc = [0, 0]
        # for each in self.channels[0].event_buffer.slots[self.channels[0].event_buffer.present].anticipations:
        #     if self.channels[0].event_buffer.slots[self.channels[0].event_buffer.present].anticipations[each].solved:
        #         acc[0] += 1
        #     acc[1] += 1
        # self.tmp.append(acc[0] / (acc[1] + 0.001))
        # print("Anticipation Hit Rate:", acc[0] / (acc[1] + 0.001))
        # ==============================================================================================================

        print("================================")
        print("num of questions: ", len(self.questions))
        print("num of new questions: ", len(self.new_questions))
        print("solved questions: ", len(self.solved_questions))
        print("solved new questions: ", len(self.solved_new_questions))
        print("cycle: ", self.cycle_count)
        self.cycle_count += 1

        # TODO, do I really need a return?
        # return tasks_derived, judgement_revised, goal_revised, answers_question, answers_quest, (None, None)

    def click_button(self):
        text = self.input_textEdit.toPlainText()
        self.input_textEdit.clear()
        additional_info = ""
        if text != "":
            additional_info += "<b> <font color='red'> User Input Succeed </font> </b> : <br> <br>"
            additional_info += escape(text).replace("\n", "<br>") + "<hr> </hr>"
            text = text.split("\n")
            self.input_lines(text)
        start_time = time.time()
        self.cycle()
        end_time = time.time()
        additional_info += "<font color='green'> <b> Running Time </b>: " + str(
            format(end_time - start_time, ".3f")) + " (s) <hr> </hr> </font>"
        additional_info += "<b> (1) Cycle(s) Finished </b> <hr> </hr>"
        self.show_content(self.content(additional_info))

    def click_buttons(self):
        text = self.input_textEdit.toPlainText()
        self.input_textEdit.clear()
        additional_info = ""
        if text != "":
            additional_info += "<b> <font color='red'> User Input Succeed </font> </b> : <br> <br>"
            additional_info += escape(text).replace("\n", "<br>") + "<hr> </hr>"
            text = text.split("\n")
            self.input_lines(text)
        start_time = time.time()
        self.cycles(self.spinBox.value())
        end_time = time.time()
        additional_info += "<font color='green'> <b> Running Time </b>: " + str(
            format(end_time - start_time, ".3f")) + " (s) <hr> </hr> </font>"
        additional_info += "<b> (" + str(self.spinBox.value()) + ") Cycle(s) Finished </b> <hr> </hr>"
        self.show_content(self.content(additional_info))

    def content(self, additional_info):
        ret = {"output_buffer": self.output_buffer.content(additional_info),
               "internal_buffer": self.internal_buffer.content(),
               "global_buffer": self.global_buffer.content()}
        for each in self.channels:
            ret[each.ID] = each.event_buffer.content()
        return ret
