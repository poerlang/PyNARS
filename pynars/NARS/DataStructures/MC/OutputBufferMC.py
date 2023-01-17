from pynars.GUI.Ui_Form import escape
from pynars.Narsese import Task, Compound, Interval, Term


class OutputBufferMC:

    def __init__(self):
        self.agenda_length = 20
        self.operation_of_channel = {}
        self.channel_of_operation = {}
        self.agenda = {i: [] for i in range(self.agenda_length)}

        self.active_questions = []
        self.active_goals = []

    def register_channel(self, channel):  # register channels' operations
        tmp = set()
        for each_operation in channel.operations:
            tmp.add(each_operation)
            self.operation_of_channel.update({each_operation: channel})
        self.channel_of_operation.update({channel: tmp})

    def decompose(self, term: Term, agenda_pointer):
        # decompose complicated compound operations, including intervals
        ap = agenda_pointer
        if isinstance(term, Compound):
            for each_component in term.terms:
                if isinstance(each_component, Interval):
                    ap += each_component.interval
                elif isinstance(each_component, Compound):
                    self.decompose(each_component, ap)
                else:
                    for each_operation in self.operation_of_channel:
                        if each_component.equal(each_operation) and ap < self.agenda_length:  # only store operations
                            self.agenda[ap].append(each_component)
                            break
        else:
            self.agenda[ap].append(term)

    def distribute_execute(self):  # distribute the decomposed operations into corresponding channels
        for each_operation in self.agenda[0]:
            corresponding_channel = self.operation_of_channel[Term("^" + each_operation.word)]
            corresponding_channel.execute(Term("^" + each_operation.word))  # operation execution
            corresponding_channel.event_buffer.slots[corresponding_channel.event_buffer.present].update_operations(
                Term("^" + each_operation.word))  # operation execution record added
        self.agenda = {i: self.agenda[i + 1] for i in range(self.agenda_length - 1)}
        self.agenda.update({self.agenda_length - 1: []})

    def step(self, task: Task):
        """
        This function is used to distribute "operations" from the internal buffer to the event buffer.
        One operation goal is firstly generated in the inference engine. After that, it will be forwarded to the
        internal buffer, and if this task is further forwarded to the global buffer, this task will be viewed as
        "executed". And it is also really executed, which might be reflected in the information gathered by the
        corresponding event buffer. And it is possible for the global buffer to generate "procedural knowledge".

        Since such operation is executed by the event buffer, it also needs to be "percepted" by the event buffer.
        And so in event buffers, it is also possible to generate such "procedural knowledge".

        In short, this function will execute the operation goal selected from the internal buffer and let the
        corresponding event buffer know.
        """
        # operation goal
        if task and task.is_goal:
            self.decompose(task.term, 0)
            self.distribute_execute()

    def reset(self):
        self.agenda = {i: [] for i in range(self.agenda_length)}
        self.active_questions = []
        self.active_goals = []

    def content(self, additional_info):
        ret = "<p style=\"text-align: left\"> <hr> </hr>" + additional_info + "Active Questions: "
        if len(self.active_questions) != 0:
            ret += "<br>"
            for each in self.active_questions:
                ret += "<font color='red'>" + str(format(each.truth.f, ".3f")) + "</font> | <font color='blue'>" + str(
                    format(each.truth.c, ".3f")) + "</font> <br> <b>" + escape(
                    each.term.word) + "</b> <br> <font color='green'>" + str(
                    format(each.budget.priority, ".3f")) + " | " + str(
                    format(each.budget.durability, ".3f")) + " | " + str(
                    format(each.budget.quality, ".3f")) + "</font> <hr> </hr>"
        else:
            ret += "None <hr> </hr>"
        ret += "Active Goals: "
        if len(self.active_goals) != 0:
            ret += "<br>"
            for each in self.active_goals:
                ret += "<font color='red'>" + str(format(each.truth.f, ".3f")) + "</font> | <font color='blue'>" + str(
                    format(each.truth.c, ".3f")) + "</font> <br> <b>" + escape(
                    each.term.word) + "</b> <br> <font color='green'>" + str(
                    format(each.budget.priority, ".3f")) + " | " + str(
                    format(each.budget.durability, ".3f")) + " | " + str(
                    format(each.budget.quality, ".3f")) + "</font> <hr> </hr>"
        else:
            ret += "None <hr> </hr>"
        return ret
