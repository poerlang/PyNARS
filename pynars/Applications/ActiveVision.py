import random

import cv2
import numpy as np
import torch
from matplotlib import pyplot as plt

from pynars import Global
from pynars.NAL.Functions import Truth_revision
from pynars.NARS.DataStructures import Memory
from pynars.NARS.DataStructures.MC.SlotMC import SlotMC
from pynars.NARS.InferenceEngine import GeneralEngine
from pynars.Narsese import Task, Judgement, Compound, Term, Statement, Copula, Stamp, Base
from pynars.utils.MNIST_data import data_train, data_test, MNIST_num


def stamp_generator():
    return Stamp(Global.time, None, None, Base((Global.get_input_id(),)))


class PrototypeManager:

    def __init__(self, threshold):
        self.threshold = threshold
        self.prototype_ID = 0
        self.prototypes = {"P_0": np.zeros((8, 8))}  # initial empty prototype

    def check_image_patch(self, img):

        # plt.figure()
        # plt.imshow(img)
        # plt.show()

        # resize to a fixed size (8x8)
        img = cv2.resize(img.astype(np.float64), (8, 8))

        # blur the image patch to deal with noises
        if de_noise:
            gaussian_noise = np.random.normal(0, 0.1, img.shape)
            img_blur = img + gaussian_noise
        else:
            img_blur = img + np.zeros(img.shape)

        # compare with all existed prototypes, find the candidate prototype, or create a new prototype
        img_patch_ID = None
        for each_ID in self.prototypes:
            # print(np.mean(np.abs(img_blur - self.prototypes[each_ID])))
            if np.mean(np.abs(img_blur - self.prototypes[each_ID])) < self.threshold:
                img_patch_ID = each_ID
                break
        if img_patch_ID is None:
            self.prototype_ID += 1
            img_patch_ID = "P_" + str(self.prototype_ID)
            self.prototypes.update({img_patch_ID: img_blur})

        # give the image patch the name of the prototype
        return img_patch_ID, self.prototypes[img_patch_ID]

    @property
    def num_prototype(self):
        return self.prototype_ID + 1

    def show_prototype(self, i):
        plt.figure()
        plt.xticks([])
        plt.yticks([])
        plt.imshow(self.prototypes["P_" + str(i)])
        plt.show()

    def show_prototypes(self):
        plt.figure()
        for j in range(25):
            ID = "P_" + str(j)
            if ID in self.prototypes:
                plt.subplot(5, 5, j + 1)
                plt.xticks([])
                plt.yticks([])
                plt.imshow(self.prototypes[ID])
            else:
                plt.show()
                return
        plt.show()
        for i in range(1, (self.prototype_ID + 1) // 25):
            plt.figure()
            for j in range(25):
                ID = "P_" + str(25 * i + j)
                if ID in self.prototypes:
                    plt.subplot(5, 5, j + 1)
                    plt.xticks([])
                    plt.yticks([])
                    plt.imshow(self.prototypes[ID])
                else:
                    plt.show()
                    return
            plt.show()


class ImageTracer:

    def __init__(self, img, label: int, threshold):
        # initialization
        self.original_img = img
        self.original_img_label = "num" + str(label)
        self.starting_point = np.array((0, 0))
        self.threshold = threshold
        # tracer
        self.patch_size = np.array((12, 12))
        self.current_point = np.array((0, 0))
        self.current_pattern = np.zeros(img.shape)
        # history
        self.previous_point = np.array((0, 0))
        self.operation_sequence = []

    def step(self, operation: Term, prototype_manager: PrototypeManager, target: np.array):
        current_pattern_ID = None
        current_pattern_label = None
        image_patch_ID = None

        current_point = self.current_point.copy()
        patch_size = self.patch_size.copy()
        if operation.word == "^left":
            current_point[0] = self.previous_point[0] - self.patch_size[0] // 2
            # print("left")
        elif operation.word == "^right":
            current_point[0] = self.previous_point[0] + self.patch_size[0] // 2
            # print("right")
        elif operation.word == "^up":
            current_point[1] = self.previous_point[1] - self.patch_size[1] // 2
            # print("up")
        elif operation.word == "^down":
            current_point[1] = self.previous_point[1] + self.patch_size[1] // 2
            # print("down")
        elif operation.word == "^zoomIn":
            patch_size -= np.array((2, 2))
            # print("zoom in")
        elif operation.word == "^zoomOut":
            patch_size += np.array((2, 2))
            # print("zoom out")
        else:
            print("undefined operation")
        if current_point[0] < 0 or \
                current_point[1] < 0 or \
                current_point[0] >= self.original_img.shape[0] or \
                current_point[1] >= self.original_img.shape[1] or \
                patch_size[0] < 8 or \
                patch_size[0] >= self.original_img.shape[0] or \
                current_point[0] + patch_size[0] >= self.original_img.shape[0] or \
                current_point[1] + patch_size[1] >= self.original_img.shape[1]:
            return False, image_patch_ID, current_pattern_ID, current_pattern_label  # invalid operation

        self.operation_sequence.append(operation.word)
        self.previous_point = self.current_point
        self.current_point = current_point
        self.patch_size = patch_size

        image_patch = self.original_img[self.current_point[0]:self.current_point[0] + self.patch_size[0],
                      self.current_point[1]:self.current_point[1] + self.patch_size[1]]
        image_patch_ID, image_patch_prototype = prototype_manager.check_image_patch(image_patch)
        resized_prototype = cv2.resize(image_patch_prototype, self.patch_size)

        self.current_pattern[self.current_point[0]:self.current_point[0] + self.patch_size[0],
        self.current_point[1]:self.current_point[1] + self.patch_size[1]] = resized_prototype

        # plt.figure()
        # plt.imshow(self.current_pattern)
        # plt.show()

        # make the current pattern a prototype:
        current_pattern_ID, current_pattern_prototype = prototype_manager.check_image_patch(self.current_pattern)

        # de-noise
        if de_noise:
            gaussian_noise = np.random.normal(0, 0.1, current_pattern_prototype.shape)
            target_blur = cv2.resize(target.astype(np.float64), current_pattern_prototype.shape) + gaussian_noise
        else:
            target_blur = cv2.resize(target.astype(np.float64), current_pattern_prototype.shape)

        if np.mean(np.abs(current_pattern_prototype - target_blur)) < self.threshold:
            current_pattern_label = self.original_img_label

        return True, image_patch_ID, current_pattern_ID, current_pattern_label


class PredictionManager:

    def __init__(self, num_prediction):
        self.num_prediction = num_prediction
        self.predictions: [Judgement] = [Judgement(Term("(&/, P_0, ^zoomOut)."), stamp=stamp_generator())]

    def check_predict(self, tasks, event):
        """
        All predictions have no budget, they just have the truth-value.
        By using one of the predictions, if the task (backward task stored) can be achieved, then this prediction
        will have the budget of that task.
        """
        candidate_predictions = []
        for each_task in tasks:
            for each_prediction in self.predictions:
                if each_prediction.term.predicate.equal(each_task.term):
                    if each_prediction.term.subject.terms[0].equal(event.term):
                        candidate_predictions.append(Task(each_prediction, each_task.budget))
        if len(candidate_predictions) != 0:
            candidate_predictions.sort(key=lambda x: x.budget.priority)
            operation = candidate_predictions[-1].sentence.term.subject.terms[-1]
            return operation

    def update_prediction(self, judgement):
        existed = False
        for i in range(len(self.predictions)):
            if self.predictions[i].term.equal(judgement.term):
                existed = True
                tmp = Judgement(judgement.term, truth=Truth_revision(self.predictions[i].truth, judgement.truth),
                                stamp=stamp_generator())
                self.predictions = self.predictions[:i] + self.predictions[i + 1:]
                self.predictions.append(tmp)
                break
        if not existed:
            self.predictions.append(judgement)
        if len(self.predictions) > self.num_prediction:
            self.predictions = self.predictions[1:]


class EventBufferMC:

    def __init__(self, num_slot, num_event, num_anticipation, num_operation, num_prediction, memory: Memory,
                 prototype_manager: PrototypeManager, image_tracer: ImageTracer):
        # each slot
        self.num_event = num_event
        self.num_anticipation = num_anticipation
        self.num_operation = num_operation
        self.num_prediction = num_prediction
        # slots
        self.num_slot = num_slot * 2 + 1
        self.present = num_slot
        self.slots = [SlotMC(num_event, num_anticipation, num_operation) for _ in range(self.num_slot)]
        # memory
        self.memory = memory
        # prediction
        self.prediction_manager = PredictionManager(num_prediction)
        # prototype manager
        self.prototype_manager = prototype_manager
        # image tracer
        self.image_tracer = image_tracer
        # initialization
        self.slots[self.present + 1].operations.append(Term("^zoomOut"))
        self.slots[self.present].update_events(Task(Judgement(Term("P_0"), stamp=stamp_generator())))
        self.slots[self.present].candidate = Task(Judgement(Term("P_0"), stamp=stamp_generator()))

    def compound_generation(self):
        task_for_memory = []
        operation_todo: Term = self.slots[self.present].operations[0]
        success, patch_ID, pattern_ID, pattern_label = self.image_tracer.step(operation_todo,
                                                                              self.prototype_manager,
                                                                              self.image_tracer.original_img)
        if not success:  # invalid operation, did nothing
            self.slots[self.present].events = self.slots[self.present - 1].events
            self.slots[self.present].candidate = self.slots[self.present - 1].candidate
            # TODO, should punish the unsuccessful predictions
            return task_for_memory

        self.slots[self.present].update_events(Task(Judgement(Term(patch_ID), stamp=stamp_generator())))  # e.g., P_2
        term_1 = self.slots[self.present - 1].candidate.term
        term_2 = operation_todo
        term_3 = self.slots[self.present].events[0][1].term
        term = Compound.SequentialEvents(*[term_1, term_2, term_3])
        self.slots[self.present].candidate = Task(
            Judgement(term, stamp=stamp_generator()))  # e.g., (&/, P_1 , ^opt, P_2), cpd.

        if pattern_ID is not None:
            task_for_memory.append(
                Task(Judgement(Statement(term, Copula.Inheritance, Term(pattern_ID)), stamp=stamp_generator())))
        if pattern_label is not None:
            task_for_memory.append(
                Task(Judgement(Statement(Term(pattern_ID), Copula.Inheritance, Term(pattern_label)),
                               stamp=stamp_generator())))

        return task_for_memory

    def local_and_memory_based_evaluation(self, random_operation: Term, backward_tasks):

        # print(self.prediction_manager.predictions)

        operation: Term = self.prediction_manager.check_predict(backward_tasks, self.slots[self.present].events[0][1])
        if operation is None:
            operation = random_operation
        self.slots[self.present + 1].operations.append(operation)

    def prediction_generation(self):
        term_1 = self.slots[self.present - 1].events[0][1].term
        term_2 = self.slots[self.present].operations[0]
        subject_term = Compound.SequentialEvents(*[term_1, term_2])
        predict_term = self.slots[self.present].events[0][1].term
        prediction = Judgement(Statement(subject_term, Copula.PredictiveImplication, predict_term),
                               stamp=stamp_generator())
        self.prediction_manager.update_prediction(prediction)

    def reset(self, img, label):
        self.slots = [SlotMC(self.num_event, self.num_anticipation, self.num_operation) for _ in range(self.num_slot)]
        self.image_tracer = ImageTracer(img, label.item(), self.image_tracer.threshold)
        self.slots[self.present + 1].operations.append(Term("^zoomOut"))
        self.slots[self.present].update_events(Task(Judgement(Term("P_0"), stamp=stamp_generator())))
        self.slots[self.present].candidate = Task(Judgement(Term("P_0"), stamp=stamp_generator()))

    def step(self, random_operation, backward_tasks):
        task_forward = []

        # remove the oldest slot and create a new one
        self.slots = self.slots[1:]
        self.slots.append(SlotMC(self.num_event, self.num_anticipation, self.num_operation))

        task_for_memory = self.compound_generation()
        task_forward.extend(task_for_memory)
        self.local_and_memory_based_evaluation(random_operation, backward_tasks)
        self.prediction_generation()

        task_forward.append(self.slots[self.present].candidate)

        return task_forward


class ActiveVisionChannel:

    def __init__(self, event_buffer):
        self.operations = [Term("^up"), Term("^down"), Term("^left"), Term("^right"), Term("^zoomIn"), Term("^zoomOut")]
        self.event_buffer = event_buffer

    def reset(self, img, label):
        self.event_buffer.reset(img, label)

    def step(self, backward_tasks):
        random_operation = np.random.choice(self.operations, 1).item()
        return self.event_buffer.step(random_operation, backward_tasks)

# hyper parameter
num = [3, 8, 9]
num_train = 40
num_test = 10
de_noise = False
large_loop = 1  # go through the entire training set
small_loop = 10  # how many steps for each individual training case
system_cycle = 1  # how many system cycles for each small step
num_slot = 2
num_event = 10
num_anticipation = 10
num_operation = 10
num_prediction = 100
num_backward_tasks = 50
num_inference_results = 50
prototype_threshold = 0.15
image_similarity_threshold = 0.05

# data structures
dataloader_train = torch.utils.data.DataLoader(dataset=data_train, batch_size=1, shuffle=True)
dataloader_test = torch.utils.data.DataLoader(dataset=data_test, batch_size=1, shuffle=True)
train, test = MNIST_num(num=num, num_train=num_train, num_test=num_test, dataloader_train=dataloader_train,
                        dataloader_test=dataloader_test, shape=(32, 32))
backward_tasks = []
inference_results = []
memory = Memory(100)
prototype_manager = PrototypeManager(threshold=prototype_threshold)
image_tracer = ImageTracer(train[0][0], train[0][1].item(), threshold=image_similarity_threshold)
EBF = EventBufferMC(num_slot, num_event, num_anticipation, num_operation, num_prediction, memory,
                    prototype_manager, image_tracer)
AVC = ActiveVisionChannel(EBF)
reasoner = GeneralEngine()

for _ in range(large_loop):
    # print("===")
    for tc, each in enumerate(train):
        # print("---")
        AVC.reset(each[0], each[1])
        inference_results = []
        for sl in range(small_loop):
            # print(">>>")

            tasks_for_memory = AVC.step(backward_tasks)
            if len(inference_results) > 0:
                tasks_for_memory.append(inference_results[0])
                inference_results = inference_results[1:]

            for each_task in tasks_for_memory:

                if each_task is None:
                    continue

                # record backward tasks
                if each_task.is_question or each_task.is_goal:
                    backward_tasks.append(each_task)
                if len(backward_tasks) > num_backward_tasks:
                    backward_tasks = backward_tasks[-num_backward_tasks:]

                # memory accept these tasks
                task_revised, goal_derived, answers_question, answer_quest = memory.accept(each_task)
                if task_revised is not None:
                    inference_results.append(task_revised)
                if goal_derived is not None:
                    for each_goal_derived in goal_derived:
                        for i in range(len(backward_tasks)):
                            if backward_tasks[i].term.equal(each_goal_derived.term):
                                backward_tasks = backward_tasks[:i] + backward_tasks[i + 1:]
                                break
                if answers_question is not None:
                    for each_answer_question in answers_question:
                        for i in range(len(backward_tasks)):
                            if backward_tasks[i].term.equal(each_answer_question.term):
                                backward_tasks = backward_tasks[:i] + backward_tasks[i + 1:]
                                break

            for _ in range(system_cycle):
                concept = memory.take(remove=True)
                if concept is not None:
                    tasks_derived, _ = reasoner.step(concept)
                    inference_results.extend(tasks_derived)
                    memory.put_back(concept)
                Global.time += 1

        if tc > int(0.7 * num_train):
            plt.imshow(AVC.event_buffer.image_tracer.current_pattern)
            plt.show()

prototype_manager.show_prototypes()
