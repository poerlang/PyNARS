from copy import copy
from typing import Type, Union

from .Budget import Budget
from .Item import Item
from .Sentence import Sentence, Judgement, Goal, Quest, Question, Stamp
from .Term import Term
from .Truth import Truth


class Task(Item):
    """
    Two new defined property: parent_task, generated_tasks.
    A new defined function: withdraw_brothers.

    I am not sure whether they are needed. These two things are for reducing the priority of co-generated backward tasks
    when one of them is solved.

    Say to solve one question, I have generated 10 sub-questions, and when one of them is solved, this means the
    problem itself is solved, and the other 9 sub-questions are no longer needed.

    But this does not mean these sub-questions are completely deleted, but their priority if reduced to the
    proportion from the solved question. Though currently, for convenience, it is decreased to 30% of the previous
    one.
    """

    input_id = -1

    def __init__(self, sentence: Sentence, budget: Budget = None, input_id: int = None) -> None:
        super().__init__(hash(sentence), budget)

        self.parent_task = None
        self.generated_tasks = []  # so far it is only for the backward tasks, say questions, goals, queries.

        self.sentence: Sentence = sentence
        self.input_id = self.input_id if input_id is None else input_id

    def withdraw_brothers(self):
        """
        It is used to reduce the priority of these brother tasks.

        Note that this function is not a recursive function, say the withdrawal will not recursively apply to the
        parent level.
        """
        if self.parent_task:
            for each_task in self.parent_task.generated_tasks:
                if not each_task.term.equal(self.term):
                    each_task.budget.priority *= 0.3

    def achieving_level(self, truth_belief: Truth = None):
        if self.is_judgement:
            e_belief = truth_belief.e if truth_belief is not None else 0.5
            judgement: Judgement = self.sentence
            return 1 - abs(judgement.truth.e - e_belief)
        elif self.is_goal:
            e_belief = truth_belief.e if truth_belief is not None else 0.5
            goal: Goal = self.sentence
            return 1 - abs(goal.truth.e - e_belief)
        elif self.is_question:
            question: Question = self.sentence
            return truth_belief.e if question.is_query else truth_belief.c
        elif self.is_quest:
            quest: Quest = self.sentence
            return truth_belief.e if quest.is_query else truth_belief.c
        else:
            raise f'Invalid type! {type(self.sentence)}'

    def reduce_budget_by_achieving_level(self, belief_selected: Union[Type['Belief'], None]):
        truth = belief_selected.truth if belief_selected is not None else None
        self.budget.reduce_by_achieving_level(self.achieving_level(truth))

    @property
    def stamp(self) -> Stamp:
        return self.sentence.stamp

    @property
    def evidential_base(self):
        return self.sentence.evidential_base

    @property
    def term(self) -> Term:
        return self.sentence.term

    @property
    def truth(self) -> Truth:
        return self.sentence.truth

    @property
    def is_judgement(self) -> bool:
        return self.sentence.is_judgement

    @property
    def is_goal(self) -> bool:
        return self.sentence.is_goal

    @property
    def is_question(self) -> bool:
        return self.sentence.is_question

    @property
    def is_quest(self) -> bool:
        return self.sentence.is_quest

    @property
    def is_query(self) -> bool:
        return self.term.has_qvar and (self.is_question or self.is_quest)

    @property
    def is_eternal(self) -> bool:
        return self.sentence.is_eternal

    @property
    def is_event(self) -> bool:
        return self.sentence.is_event

    @property
    def is_external_event(self) -> bool:
        return self.sentence.is_external_event

    @property
    def is_operation(self) -> bool:
        return self.term.is_operation

    @property
    def is_mental_operation(self) -> bool:
        return self.term.is_mental_operation

    @property
    def is_executable(self):
        return self.is_goal and self.term.is_executable

    def eternalize(self, truth: Truth = None):
        task = copy(self)
        task.sentence = task.sentence.eternalize(truth)
        return task

    def __str__(self) -> str:
        """
        $p;d;q$ sentence %f;c%
        """
        return f'{(str(self.budget) if self.budget is not None else "$-;-;-$") + " "}{self.sentence.repr(False)}'

    def __repr__(self) -> str:
        return str(self)


Belief = Task
Desire = Task
