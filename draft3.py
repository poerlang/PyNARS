"""
This draft is a demo for a "minimal model" of the system implemented with the "correct" control mechanism.

Some details about this demo:
The system has four parts: 1) core, 2) user input (UI), 3) observations (obs), 4) filter.

Core. Is the core of NARS considering only the main-cycle, starting at getting one concept out (or accepting a new
task if there is one), ending after applying reasoning rules and generate new tasks.

UI. This UI is still directly connected to the memory of the core. But differently, Narsese inputs through UI will not
have a default budget (though default truth value). This is because the UI is for the "user (VIP)", and so everything
should be of the highest priority. And so the task (or its related concept) should be placed in the bucket in the
memory with the highest probability to be processed in the next X rounds of reasoning (X is the number of buckets).
So, its budget will be applied "autonomously".

Obs. This is the event buffer in OpenNARS 3.1.3, equipped with temporal and spatial reasoning ability. It will
"automatically" gather information (Narsese) in its observing environment. But (merely) in this gathering process,
the Narsese sentences generated will have a very low budget. This budget might be increased in the "memory-based
evaluation" process as (or through some budget functions) the related concept. This is also very natural.

Filter. From OpenNARS 3.1.0's conceptual design, there are four "status evaluations" mentioned: 1) satisfaction, 2)
alertness, 3) busyness, 4) well-being. Since the last evaluation (well-being) is related to the hard-ward of the AI
agent, and so it is omitted here. As well as the first evaluation, since no emotions (NAL-9) will be mentioned here,
it will also be omitted. For the other 2 evaluations, they will be used to filter the (maybe many) generated
tasks. Say for alertness, "if the system recent processing is not fruitful, some fruitful tasks (judgments) will be
preferred". For busyness, "if the system's budgets are not in good condition (e.g., so many high-priority tasks
), no task will be forwarded". And this will be a priority queue.
"""
import random
from typing import List

import numpy as np

from pynars import Config, Global
from pynars.NAL.Functions import truth_to_quality
from pynars.NARS.DataStructures import Memory, Concept
from pynars.NARS.DataStructures.MC.ChannelMC import ChannelMC
from pynars.NARS.InferenceEngine import GeneralEngine
from pynars.Narsese import parser, Truth
from pynars.SampleChannels.SinglePendulum import SinglePendulum


class Filter:

    def __init__(self, capacity = 20):
        self.capacity = capacity
        self.tasks = []
        self.alertness = 0  # whether the knowledge of the system is enough for solving problems (non-judgments)
        # alertness is from 0 to 1, (1 - alertness) is the punishment for non-judgment tasks
        # it is calculated by the number of non-successful non-judgment tasks solving in K (10 by default) cycles
        self.busyness = 0  # busyness is the average of the priority of all concepts in the memory
        # it is from 0 to 1, (1 - busyness) is the probability for the Filter pop one task to the memory

    def filter(self):
        for i in range(len(self.tasks)):
            if self.tasks[i][0].truth is not None:
                truthEXP = self.tasks[i][0].truth.e
            else:
                truthEXP = 0.3
            priority = self.tasks[i][0].budget.priority
            if not self.tasks[i][0].is_judgement:
                a = 1 - self.alertness
            else:
                a = 1
            self.tasks[i][1] = truthEXP * priority * a
        self.tasks.sort(key=lambda x: x[1])
        if len(self.tasks) > self.capacity:
            self.tasks = self.tasks[:self.capacity]

    def add_new_task(self, task):
        # duplicate tasks (probably different budgets and truth-values) are allowed
        if task is not None:
            self.tasks.append([task, 0])

    def step(self, alertness, busyness):
        self.alertness = alertness
        self.busyness = busyness
        self.filter()
        if random.random() > self.busyness:
            return self.tasks[0][0]
        else:
            return None


class MinimalReasonerMC:

    def __init__(self, n_memory, config = './config.json') -> None:

        Config.load(config)
        self.inference = GeneralEngine()  # general rule engine
        self.memory = Memory(n_memory)
        self.channels: List[ChannelMC] = [
            SinglePendulum(3, 5, 10, 10, 10, self.memory, "Channel_1"),
        ]

        self.num_channels = len(self.channels)
        self.num_slots = 3 * 2 + 1

        self.filter = Filter()
        self.alertness = []
        self.alertness_size = 10
        self.busyness = 0

    def input_lines(self, texts: List[str]):
        """
        collect the content in the input window; parse them into Narsese and process;
        a task will be directly accepted (accept()) by the main memory
        """
        for text in texts:
            if text:
                t = parser.parse(text)
                task_revised, goal_derived, answer_question, answer_quest = self.memory.accept(t)
                if task_revised is not None:
                    self.filter.add_new_task(task_revised)
                if goal_derived is not None:
                    self.filter.add_new_task(goal_derived)
                if answer_question is not None:
                    self.filter.add_new_task(answer_question)
                if answer_quest is not None:
                    self.filter.add_new_task(answer_quest)

    def cycles(self, n_cycle: int):
        for _ in range(n_cycle):
            self.cycle()

    def cycle(self):
        """
        Everything to do by NARS in a single working cycle
        """
        self.busyness = 0
        for each_concept in self.memory.concepts:
            self.busyness += each_concept.budget.priority
        self.busyness /= len(self.memory.concepts)

        # step 1, take one task from the filter and make it accepted (accept()) by the memory
        task_from_filter = self.filter.step(1 - sum(self.alertness) / self.alertness_size, self.busyness)
        task_revised, goal_derived, answer_question, answer_quest = self.memory.accept(task_from_filter)
        if task_revised is not None:
            self.filter.add_new_task(task_revised)
        if goal_derived is not None:
            self.filter.add_new_task(goal_derived)
        if answer_question is not None:
            self.filter.add_new_task(answer_question)
        if answer_quest is not None:
            self.filter.add_new_task(answer_quest)

        # step 2, take out a task from each channel and make it accepted (accept()) by the memory
        for i, each_channel in enumerate(self.channels):
            task_revised, goal_derived, answer_question, answer_quest = self.memory.accept(each_channel.step())
            if task_revised is not None:
                self.filter.add_new_task(task_revised)
            if goal_derived is not None:
                self.filter.add_new_task(goal_derived)
            if answer_question is not None:
                self.filter.add_new_task(answer_question)
            if answer_quest is not None:
                self.filter.add_new_task(answer_quest)

        # step 3, apply general inference step
        concept: Concept = self.memory.take(remove=True)
        if concept is not None:
            tasks_inference_derived, T = self.inference.step(concept)  # updating the alertness and busyness from here
            if T:
                self.alertness.append(1)
            else:
                self.alertness.append(0)
            if len(self.alertness) > self.alertness_size:
                self.alertness = self.alertness[1:]
            for each in tasks_inference_derived:
                self.filter.add_new_task(each)
            self.memory.put_back(concept)

        # handle the sense of time
        Global.time += 1

    def user_input(self, text):
        stable_distribution = [0.018, 0.019, 0.021, 0.024, 0.028, 0.032, 0.039, 0.048, 0.064, 0.096, 0.193]
        stable_distribution = stable_distribution[::-1]

        # bucket localization
        for i in range(len(stable_distribution)):  # search the last 10 buckets in the memory
            stable_distribution[i] /= 1 + len(self.memory.concepts.levels[-i])

        priority = 1 - np.argmax(stable_distribution) / self.memory.concepts.n_levels
        durability = 0.8
        quality = truth_to_quality(Truth(1, 0.99, 1))

        task = parser.parse(
            "$" + str(priority) + ";" + str(durability) + ";" + str(quality) + "$ " + text + " %1;0.99%")
        task_revised, goal_derived, answer_question, answer_quest = self.memory.accept(task)
        if task_revised is not None:
            self.filter.add_new_task(task_revised)
        if goal_derived is not None:
            self.filter.add_new_task(goal_derived)
        if answer_question is not None:
            self.filter.add_new_task(answer_question)
        if answer_quest is not None:
            self.filter.add_new_task(answer_quest)

    def main(self):
        """
        run the experiment
        """
        user_input_sequence = {20: "<L =/> R>?",
                               100: "<L =/> R>?"}

        for i in range(1000):  # 1000 cycles by default
            if i in user_input_sequence:
                self.user_input(user_input_sequence[i])
            self.cycle()
