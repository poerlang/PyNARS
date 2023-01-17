from abc import abstractmethod

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


def escape(text):
    return text.replace("&", "&amp;").replace(">", "&gt;").replace("<", "&lt;")


class Ui_Form(object):

    def __init__(self):
        self.IDC = {}  # channel ID: channel Index
        self.num_channels = 0
        self.num_slots = 0
        self.IDs = []

    @abstractmethod
    def click_button(self):
        pass

    @abstractmethod
    def click_buttons(self):
        pass

    def show_content(self, content):
        """
        content is a big dictionary, each channel and each slot will contribute to one of them.
        e.g.,
        content = {"output_buffer":[[[A,E,O],[A,E,O],[A,E,O],[A,E,O],[A,E,O]],P], "internal buffer":[],
        "global_buffer":[], "XX_channel":[]}
        """
        for each in content:
            if each == "output_buffer":
                self.output_textBrowser.setText(content[each])
            elif each == "internal_buffer":
                AEOs, P = content[each]
                self.predictions_textBroswer[0].setHtml(P)
                for i in range(self.num_slots):
                    A, E, O = AEOs[i]
                    self.anticipations_textBrowser[0][i].setHtml(A)
                    self.events_textBrowser[0][i].setHtml(E)
                    self.operations_textBrowser[0][i].setHtml(O)
            elif each == "global_buffer":
                AEOs, P = content[each]
                self.predictions_textBroswer[1].setHtml(P)
                for i in range(self.num_slots):
                    A, E, O = AEOs[i]
                    self.anticipations_textBrowser[1][i].setHtml(A)
                    self.events_textBrowser[1][i].setHtml(E)
                    self.operations_textBrowser[1][i].setHtml(O)
            else:
                channel_idx = self.IDC[each]
                AEOs, P = content[each]
                self.predictions_textBroswer[channel_idx].setHtml(P)
                for i in range(self.num_slots):
                    A, E, O = AEOs[i]
                    self.anticipations_textBrowser[channel_idx][i].setHtml(A)
                    self.events_textBrowser[channel_idx][i].setHtml(E)
                    self.operations_textBrowser[channel_idx][i].setHtml(O)

    def setupUi(self, Form):

        if not Form.objectName():
            Form.setObjectName(u"Form")

        Form.resize(1920, 1050)
        # main layout setting (contains only the left_right splitter)
        self.main_layout = QGridLayout(Form)
        self.main_layout.setObjectName(u"main_layout")
        # This layout is a layout of a splitter.
        self.left_right_splitter = QSplitter(Form)
        self.left_right_splitter.setObjectName(u"left_right_splitter")
        self.left_right_splitter.setOrientation(Qt.Horizontal)
        """
        The left_right spliter contains two layouts, the left part (for user IO) and the right part (for channels).
        """
        # left widget (contains IO splitter and the button layout), you may think a widget is a "separate small world"
        self.left_widget = QWidget(self.left_right_splitter)
        self.left_widget.setObjectName(u"left__widget")
        # left layout
        self.left_layout = QGridLayout(self.left_widget)
        self.left_layout.setObjectName(u"left_layout")
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        # This layout is a layout of a splitter and another layout.

        # IO splitter (splits input window and output window, with labels)
        # this splitter is about two layouts (input_layout and output_layout)
        self.IO_splitter = QSplitter(self.left_widget)
        self.IO_splitter.setObjectName(u"IO_splitter")
        self.IO_splitter.setOrientation(Qt.Vertical)
        # output widget (contains one text browser and one label, similar technique)
        self.output_widget = QWidget(self.IO_splitter)
        self.output_widget.setObjectName(u"output_widget")
        # output layout
        self.output_layout = QGridLayout(self.output_widget)  # the layout is about the widget (***)
        self.output_layout.setObjectName(u"output_layout")
        self.output_layout.setContentsMargins(0, 0, 0, 0)
        # output text browser
        self.output_textBrowser = QTextBrowser(self.output_widget)
        self.output_textBrowser.setObjectName(u"output_textBrowser")
        self.output_textBrowser.setToolTip("The output information of the system, it will basically cover what the"
                                           "system had just accomplished, and the currently active goals and questions."
                                           "")
        self.output_layout.addWidget(self.output_textBrowser, 1, 0, 1, 1)  # put the text browser to the layout
        # output label
        self.output_label = QLabel(self.output_widget)
        self.output_label.setObjectName(u"output_label")
        self.output_layout.addWidget(self.output_label, 0, 0, 1, 1)  # put the label to the layout
        self.IO_splitter.addWidget(self.output_widget)  # put the output widget to the splitter
        # input widget (contains one text editor and one label)
        self.input_widget = QWidget(self.IO_splitter)
        self.input_widget.setObjectName(u"input_widget")
        # input layout
        self.input_layout = QGridLayout(self.input_widget)
        self.input_layout.setObjectName(u"input_form")
        self.input_layout.setContentsMargins(0, 0, 0, 0)
        # input text editor
        self.input_textEdit = QTextEdit(self.input_widget)
        self.input_textEdit.setObjectName(u"input_textEdit")
        self.input_textEdit.setToolTip("Input Narsese by the users. The inputs will be direct accepted by the memory,"
                                       "but it might not be processed due to its priority.")
        self.input_layout.addWidget(self.input_textEdit, 1, 0, 1, 1)  # put the text editor to the layout
        # input text label
        self.input_label = QLabel(self.input_widget)
        self.input_label.setObjectName(u"input_label")
        self.input_layout.addWidget(self.input_label, 0, 0, 1, 1)  # put the label to the layout
        self.IO_splitter.addWidget(self.input_widget)  # put the input widget to the splitter
        self.left_layout.addWidget(self.IO_splitter, 0, 0, 1, 1)  # put the whole splitter to the left layout

        # button layout (contains 2 buttons and one spin box)
        self.button_layout = QHBoxLayout()
        self.button_layout.setObjectName(u"button_layout")
        # 1st button - "step"
        self.button_step = QPushButton(self.left_widget)
        self.button_step.setObjectName(u"button_step")
        self.button_step.clicked.connect(self.click_button)
        self.button_layout.addWidget(self.button_step)  # put it to the layout
        # spin box
        self.spinBox = QSpinBox(self.left_widget)
        self.spinBox.setObjectName(u"spinBox")
        self.spinBox.setMinimum(1)  # set min
        self.spinBox.setMaximum(10000)  # set max
        self.button_layout.addWidget(self.spinBox)  # put it to the layout
        # 2nd button - "x steps", x is the value in the spin box, 1 minimal
        self.button_steps = QPushButton(self.left_widget)
        self.button_steps.setObjectName(u"button_steps")
        self.button_steps.clicked.connect(self.click_buttons)
        self.button_layout.addWidget(self.button_steps)  # put it to the layout
        self.left_layout.addLayout(self.button_layout, 1, 0, 1, 1)  # put the whole layout to the left layout
        self.left_right_splitter.addWidget(self.left_widget)  # put the widget to the left_right (main) splitter
        # left layout finished

        # right widget setting
        self.right_widget = QWidget(self.left_right_splitter)
        self.right_widget.setObjectName(u"right_widget")
        # right (channel) layout setting
        self.right_layout = QGridLayout(self.right_widget)  # this is about the right widget
        self.right_layout.setObjectName(u"right_form_channels")
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        """
        The right layout contains only one widget, but we still need to create it a widget to follow the program.
        It looks like we have a folder with only one folder inside. :/
        """
        # this is the thing (the folder in the folder) contained in the above widget, another widget of channels
        self.channel_widget = QTabWidget(self.right_widget)
        self.channel_widget.setToolTip(
            "Different channels, this only shows the buffers of each channels, "
            "including the internal buffer and the global buffer.")
        """
        Note that the above widget is a TabWidget, which is a widget with multiple pages.
        """
        self.channel_widget.setObjectName(u"channel_widget")
        """
        *** Channel Creation ***
        Since NARS may contains multiple channels, a loop is needed.
        Channels will be stored in a 1D vector (i-th channel).
        Slots will be stored in a 2D matrix, which means the j-th slot of the i-th channel.
        """

        self.channel_widget_items = []
        self.channel_widget_layouts = []
        self.slot_prediction_splitters = []
        self.slots_widgets = []
        self.slots_layouts = []
        self.slots_TabWidgets = []

        self.slot_widget = [[] for _ in range(self.num_channels + 2)]
        self.slot_layout = [[] for _ in range(self.num_channels + 2)]
        self.AEO_splitter = [[] for _ in range(self.num_channels + 2)]

        self.anticipations_widget = [[] for _ in range(self.num_channels + 2)]
        self.anticipations_layout = [[] for _ in range(self.num_channels + 2)]
        self.anticipations_label = [[] for _ in range(self.num_channels + 2)]
        self.anticipations_textBrowser = [[] for _ in range(self.num_channels + 2)]

        self.events_widget = [[] for _ in range(self.num_channels + 2)]
        self.events_layout = [[] for _ in range(self.num_channels + 2)]
        self.events_label = [[] for _ in range(self.num_channels + 2)]
        self.events_textBrowser = [[] for _ in range(self.num_channels + 2)]

        self.operations_widget = [[] for _ in range(self.num_channels + 2)]
        self.operations_layout = [[] for _ in range(self.num_channels + 2)]
        self.operations_label = [[] for _ in range(self.num_channels + 2)]
        self.operations_textBrowser = [[] for _ in range(self.num_channels + 2)]

        self.predictions_widget = []
        self.predictions_layout = []
        self.predictions_label = []
        self.predictions_textBroswer = []

        self.active_button = []

        for i in range(self.num_channels + 2):  # +2 is for the internal buffer and global buffer
            """
            A page (as a widget) is created. But we may have many pages, so we will put it in a list, 
            called "channel_widget_items".
            """
            self.channel_widget_items.append(QWidget())
            # TODO, channel ID is better? :/
            self.channel_widget_items[i].setObjectName(u"channel_widget_" + str(i + 1))
            """
            Channel_widget_i layout setting. It contains one check box (button) indicating whether this channel is 
            active, and a splitter of time slots and the prediction table.
            """
            # create a layout for each channel widget item
            self.channel_widget_layouts.append(QGridLayout(self.channel_widget_items[i]))
            self.channel_widget_layouts[i].setObjectName(u"channel_layout_" + str(i + 1))
            # work on the splitter first, it contains two parts, the slots and the prediction table
            self.slot_prediction_splitters.append(QSplitter(self.channel_widget_items[i]))
            self.slot_prediction_splitters[i].setObjectName(u"slot_prediction_splitter_" + str(i + 1))
            self.slot_prediction_splitters[i].setOrientation(Qt.Horizontal)
            # widget of these slots (as a whole)
            self.slots_widgets.append(QWidget(self.slot_prediction_splitters[i]))
            self.slots_widgets[i].setObjectName(u"slots_widget_" + str(i + 1))
            # layout of the above widget
            self.slots_layouts.append(QGridLayout(self.slots_widgets[i]))
            self.slots_layouts[i].setObjectName(u"slots_layout_" + str(i + 1))
            self.slots_layouts[i].setContentsMargins(0, 0, 0, 0)
            """
            each "slots widget" is a TabWidget, but we still have another widget contained in this widget like before.
            The analogy of folders.
            """
            # slots TabWidget creation, this is the widget contained in the slot_widget[i]
            self.slots_TabWidgets.append(QTabWidget(self.slots_widgets[i]))
            self.slots_TabWidgets[i].setToolTip("Slots of different buffers, a slot contains 3 parts of information,"
                                                "1) events, 2) anticipations and 3) operations (to-do).")
            self.slots_TabWidgets[i].setObjectName(u"slots_tabWidget_" + str(i + 1))
            for j in range(self.num_slots):
                self.slot_widget[i].append(QWidget())
                self.slot_widget[i][j].setObjectName(u"slots_tabWidget_" + str(i + 1) + "_" + str(j + 1))
                # slot_layout_i creation
                self.slot_layout[i].append(QGridLayout(self.slot_widget[i][j]))
                self.slot_layout[i][j].setObjectName("slot_layout_" + str(i + 1) + "_" + str(j + 1))
                """
                Each slot contains one splitter, which splits "events (E)", "anticipations (A)" and "operations (O)".
                So, it is called a AEO splitter.
                """
                self.AEO_splitter[i].append(QSplitter(self.slot_widget[i][j]))
                self.AEO_splitter[i][j].setObjectName(u"AEO_splitter_" + str(i + 1) + "_" + str(j + 1))
                self.AEO_splitter[i][j].setOrientation(Qt.Horizontal)
                """
                This splitter contains 3 layouts, one for A, one for E, and one for O.
                """

                # work on A first, like before, create widgets
                self.anticipations_widget[i].append(QWidget(self.AEO_splitter[i][j]))
                self.anticipations_widget[i][j].setObjectName(u"anticipations_widget_" + str(i + 1) + "_" + str(j + 1))
                # then give it a layout
                self.anticipations_layout[i].append(QGridLayout(self.anticipations_widget[i][j]))
                self.anticipations_layout[i][j].setObjectName(u"anticipations_layout_" + str(i + 1) + "_" + str(j + 1))
                self.anticipations_layout[i][j].setContentsMargins(0, 0, 0, 0)
                # create the text browser
                self.anticipations_textBrowser[i].append(QTextBrowser(self.anticipations_widget[i][j]))
                self.anticipations_textBrowser[i][j].setObjectName(
                    u"anticipations_textBrowser_" + str(i + 1) + "_" + str(j + 1))
                # add the browser to the layout
                self.anticipations_layout[i][j].addWidget(self.anticipations_textBrowser[i][j], 1, 0, 1, 1)
                # create the label
                self.anticipations_label[i].append(QLabel(self.anticipations_widget[i][j]))
                self.anticipations_label[i][j].setObjectName(u"anticipations_label_" + str(i + 1) + "_" + str(j + 1))
                # add the label to the layout
                self.anticipations_layout[i][j].addWidget(self.anticipations_label[i][j], 0, 0, 1, 1)
                # add the widget to the splitter
                self.AEO_splitter[i][j].addWidget(self.anticipations_widget[i][j])

                # work on E, events_layouts creation
                self.events_widget[i].append(QWidget(self.AEO_splitter[i][j]))
                self.events_widget[i][j].setObjectName(u"events_widget_" + str(i + 1) + "_" + str(j + 1))
                # events creation, label & text
                self.events_layout[i].append(QGridLayout(self.events_widget[i][j]))
                self.events_layout[i][j].setObjectName(u"events_layout_" + str(i + 1) + "_" + str(j + 1))
                self.events_layout[i][j].setContentsMargins(0, 0, 0, 0)
                self.events_textBrowser[i].append(QTextBrowser(self.events_widget[i][j]))
                self.events_textBrowser[i][j].setObjectName(u"events_textBrowser_" + str(i + 1) + "_" + str(j + 1))
                self.events_layout[i][j].addWidget(self.events_textBrowser[i][j], 1, 0, 1, 1)
                self.events_label[i].append(QLabel(self.events_widget[i][j]))
                self.events_label[i][j].setObjectName(u"events_label_" + str(i + 1) + "_" + str(j + 1))
                self.events_layout[i][j].addWidget(self.events_label[i][j], 0, 0, 1, 1)
                self.AEO_splitter[i][j].addWidget(self.events_widget[i][j])

                # work on O, operations_layouts creation
                self.operations_widget[i].append(QWidget(self.AEO_splitter[i][j]))
                self.operations_widget[i][j].setObjectName(u"operations_layout_" + str(i + 1) + "_" + str(j + 1))
                # operations creation, label & text
                self.operations_layout[i].append(QGridLayout(self.operations_widget[i][j]))
                self.operations_layout[i][j].setObjectName(u"operations_" + str(i + 1) + "_" + str(j + 1))
                self.operations_layout[i][j].setContentsMargins(0, 0, 0, 0)
                self.operations_textBrowser[i].append(QTextBrowser(self.operations_widget[i][j]))
                self.operations_textBrowser[i][j].setObjectName(
                    u"operations_textBrowser_" + str(i + 1) + "_" + str(j + 1))
                self.operations_layout[i][j].addWidget(self.operations_textBrowser[i][j], 1, 1, 1, 1)
                self.operations_label[i].append(QLabel(self.operations_widget[i][j]))
                self.operations_label[i][j].setObjectName(u"operations_label_" + str(i + 1) + "_" + str(j + 1))
                self.operations_layout[i][j].addWidget(self.operations_label[i][j], 0, 1, 1, 1)
                self.AEO_splitter[i][j].addWidget(self.operations_widget[i][j])
                self.slot_layout[i][j].addWidget(self.AEO_splitter[i][j], 0, 2, 1, 1)
                # one slot creation finished
                self.slots_TabWidgets[i].addTab(self.slot_widget[i][j], "")

            self.slots_layouts[i].addWidget(self.slots_TabWidgets[i], 0, 0, 1, 1)
            self.slot_prediction_splitters[i].addWidget(self.slots_widgets[i])

            # predictions
            # create widget
            self.predictions_widget.append(QWidget(self.slot_prediction_splitters[i]))
            self.predictions_widget[i].setToolTip("The prediction table is shared among different slots in the same "
                                                  "buffer.")
            self.predictions_widget[i].setObjectName(u"predictions_widget_" + str(i + 1))
            # create layout
            self.predictions_layout.append(QGridLayout(self.predictions_widget[i]))
            self.predictions_layout[i].setObjectName(u"predictions_layout_" + str(i + 1))
            self.predictions_layout[i].setContentsMargins(0, 0, 0, 0)
            # add a text browser
            self.predictions_textBroswer.append(QTextBrowser(self.predictions_widget[i]))
            self.predictions_textBroswer[i].setObjectName(u"predictions_textBrowser_" + str(i + 1))
            # add the browser to the layout
            self.predictions_layout[i].addWidget(self.predictions_textBroswer[i], 1, 0, 1, 1)
            # add a label
            self.predictions_label.append(QLabel(self.predictions_widget[i]))
            self.predictions_label[i].setObjectName(u"predictions_label_" + str(i + 1))
            # add it to the layout
            self.predictions_layout[i].addWidget(self.predictions_label[i], 0, 0, 1, 1)
            # add the prediction widget to the slot_prediction splitter
            self.slot_prediction_splitters[i].addWidget(self.predictions_widget[i])
            # add the splitter to the right (channel) layout, now only one button is left
            self.channel_widget_layouts[i].addWidget(self.slot_prediction_splitters[i], 1, 0, 1, 1)
            # create a button (check box)
            self.active_button.append(QRadioButton(self.channel_widget_items[i]))
            self.active_button[i].setToolTip("Select this one will make this channel transparent to the system.")
            self.active_button[i].setObjectName(u"active_button_" + str(i + 1))
            # add it to the layout
            self.channel_widget_layouts[i].addWidget(self.active_button[i], 0, 0, 1, 1)
            # now a page is created

            # add a page to the channel widget (the tab widget)
            self.channel_widget.addTab(self.channel_widget_items[i], "")
            self.right_layout.addWidget(self.channel_widget, 0, 0, 1, 1)

            # overall combine
            self.left_right_splitter.addWidget(self.right_widget)
            self.main_layout.addWidget(self.left_right_splitter, 0, 0, 1, 1)

        self.retranslateUi(Form)

        self.channel_widget.setCurrentIndex(0)
        for i in range(self.num_channels):
            self.slots_TabWidgets[i].setCurrentIndex(i + 1)
        QMetaObject.connectSlotsByName(Form)

    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("PyNARS 3.1.3 dev", u"PyNARS 3.1.3 dev", None))
        self.output_textBrowser.setHtml(QCoreApplication.translate("Form",
                                                                   u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
                                                                   "<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
                                                                   "p, li { white-space: pre-wrap; }\n"
                                                                   "</style></head><body style=\" font-family:'MS Shell Dlg 2'; font-size:8pt; font-weight:400; font-style:normal;\">\n"
                                                                   "<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>",
                                                                   None))
        self.output_label.setText(QCoreApplication.translate("Form", u"Output Message", None))
        self.input_textEdit.setHtml(QCoreApplication.translate("Form",
                                                               u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
                                                               "<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
                                                               "p, li { white-space: pre-wrap; }\n"
                                                               "</style></head><body style=\" font-family:'MS Shell Dlg 2'; font-size:8pt; font-weight:400; font-style:normal;\">\n"
                                                               "<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>",
                                                               None))
        self.input_label.setText(QCoreApplication.translate("Form", u"User Input", None))
        self.button_step.setText(QCoreApplication.translate("Form", u"Step", None))
        self.button_steps.setText(QCoreApplication.translate("Form", u"Step(s)", None))

        for i in range(self.num_channels + 2):
            for j in range(self.num_slots):
                self.anticipations_label[i][j].setText(QCoreApplication.translate("Form", u"Anticipations", None))
                self.events_label[i][j].setText(QCoreApplication.translate("Form", u"Events", None))
                self.operations_label[i][j].setText(QCoreApplication.translate("Form", u"Operations", None))
                # naming of each time slot
                self.slots_TabWidgets[i].setTabText(self.slots_TabWidgets[i].indexOf(self.slot_widget[i][j]),
                                                    QCoreApplication.translate("Form", u"Time slot " + str(
                                                        j - self.num_slots // 2), None))
            # naming of prediction table
            self.predictions_label[i].setText(QCoreApplication.translate("Form", u"Predictions", None))
            self.active_button[i].setText(QCoreApplication.translate("Form", u"De-Active", None))
            # naming of each buffer
            self.channel_widget.setTabText(self.channel_widget.indexOf(self.channel_widget_items[0]),
                                           QCoreApplication.translate("Form", "Internal Buffer", None))
            self.channel_widget.setTabText(self.channel_widget.indexOf(self.channel_widget_items[1]),
                                           QCoreApplication.translate("Form", "Global Buffer", None))
            for j, each in enumerate(self.channel_widget_items):
                if j < 2:
                    continue
                self.channel_widget.setTabText(self.channel_widget.indexOf(each),
                                               QCoreApplication.translate("Form", self.IDs[j - 2], None))
    # retranslateUi
