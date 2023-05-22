import argparse
import os
import sys

import PySide2
import PySide2.QtWidgets
from PySide2.QtGui import QPalette, QColor
from PySide2.QtWidgets import QApplication, QWidget

from pynars.NARS.Control.ReasonerMC import ReasonerMC
from pynars.utils.Print import out_print, PrintType
from pynars.utils.tools import rand_seed


def info(title):
    print(f"""
    ============= {title} =============
    module name: {__name__}
    parent process: {os.getppid()}
    process id: {os.getpid()}
    ============={'=' * (len(title) + 2)}=============
    """)


nars = ReasonerMC(100)


class MyWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = nars
        self.ui.setupUi(self)
        palette = self.palette()
        palette.setColor(QPalette.Background, QColor(211, 208, 201))
        self.setPalette(palette)
        self.setAutoFillBackground(True)


def run_nars_MC():
    info('Console')
    seed = 1024
    rand_seed(seed)
    out_print(PrintType.COMMENT, f'rand_seed={seed}', comment_title='Setup')
    out_print(PrintType.COMMENT, 'Init...', comment_title='NARS')
    out_print(PrintType.COMMENT, 'Run...', comment_title='NARS')
    # console
    out_print(PrintType.COMMENT, 'Console.', comment_title='NARS')
    dirname = os.path.dirname(PySide2.__file__)
    plugin_path = os.path.join(dirname, "plugins", "platforms")
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path
    app = QApplication(sys.argv)
    app.setStyle("WindowsVista")
    window = MyWidget()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Parse NAL files.')
    parser.add_argument('filepath', metavar='Path', type=str, nargs='*',
                        help='file path of an *.nal file.')
    args = parser.parse_args()

    try:
        run_nars_MC()
    except KeyboardInterrupt:
        out_print(PrintType.COMMENT, 'Stop...', comment_title='\n\nNARS')

    print('Done.')
