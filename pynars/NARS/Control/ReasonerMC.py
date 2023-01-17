import time
from typing import List

from pynars import Config, Global
from pynars.GUI.Ui_Form import Ui_Form
from pynars.GUI.Ui_Form import escape
from pynars.SampleChannels.SampleChannel4 import SampleChannel4
from ..DataStructures import Memory, Task, Concept
from ..DataStructures.MC.ChannelMC import ChannelMC
from ..DataStructures.MC.GlobalBufferMC import GlobalBufferMC
from ..DataStructures.MC.InternalBufferMC import InternalBufferMC
from ..DataStructures.MC.OutputBufferMC import OutputBufferMC
from ..InferenceEngine import GeneralEngine
from ...Narsese import parser


class ReasonerMC(Ui_Form):

    def __init__(self, n_memory, config = './config.json') -> None:
        super(ReasonerMC, self).__init__()
        Config.load(config)
        self.inference = GeneralEngine()
        self.previous_inference_result = []
        self.output_buffer = OutputBufferMC()
        self.memory = Memory(n_memory, output_buffer=self.output_buffer)
        self.channels: List[ChannelMC] = [
            SampleChannel4(3, 5, 10, 10, 10, self.memory, "Channel_1"),
            SampleChannel4(3, 5, 10, 10, 10, self.memory, "Channel_2")
        ]
        self.internal_buffer = InternalBufferMC(3, 5, 10, 10, 10, self.memory)
        self.global_buffer = GlobalBufferMC(3, 5, 10, 10, 10, self.memory)
        for i, each_channel in enumerate(self.channels):
            self.IDC[each_channel.ID] = 2 + i
            self.output_buffer.register_channel(each_channel)
            self.IDs.append(each_channel.ID)
        self.num_channels = len(self.channels)
        self.num_slots = 3 * 2 + 1  # TODO, different channels may have different num_slots

    def input_lines(self, texts: List[str]):
        """
        collect the content in the input window; parse them into Narsese and process
        a task will be directly accept() by the main memory
        """
        for text in texts:
            if text:
                t = parser.parse(text)
                self.memory.accept(t)

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

        # step 1, take out a task from the internal buffer, and put it into the global buffer
        task_from_internal_buffer = self.internal_buffer.step(self.previous_inference_result, "internal")

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
        tasks_for_global_buffer = tasks_from_channels + [task_from_internal_buffer]
        tasks_for_global_buffer = list(filter(None, tasks_for_global_buffer))

        # step 5, feed these tasks to the global buffer and send the one from the global buffer to the main memory
        # this will let us know the "direct process" of processing "THIS" task
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

        # step 6, apply general inference step
        # This will include the tasks generated by processing "A NEW (different from the previous)" task.
        concept: Concept = self.memory.take(remove=True)
        tasks_derived: List[Task] = []
        if concept is not None:

            tasks_inference_derived = self.inference.step(concept)
            tasks_derived.extend(tasks_inference_derived)
            for each in tasks_derived:
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

        # self.output_buffer.UI_show()

        # return tasks_derived, judgement_revised, goal_revised, answers_question, answers_quest, (
        #     task_operation_return, task_executed)
        return tasks_derived, judgement_revised, goal_revised, answers_question, answers_quest, (None, None)

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
