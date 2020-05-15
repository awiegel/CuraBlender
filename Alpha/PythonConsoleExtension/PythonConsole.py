# Imports from QT to handle signals and slots
from PyQt5.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot

# Imports from Uranium and Cura to interact with the plugin system
from UM.Extension import Extension
from UM.Application import Application
from UM.PluginRegistry import PluginRegistry

# Imports from Uranium to enable internationalization
from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("PythonConsole")

# Imports from the python standard library to build the plugin functionality
from code import InteractiveInterpreter
import os.path
from io import StringIO
import sys
import html

# This class is a context manager for the interactive console to reroute
# the standard input, output and exception handling into my own history list
class ConsoleContextManager(list):

    # This method gets called when we enter the managed context and here
    # we override Cura's crash logging and standard (error) output
    def __enter__(self):
        self._stdout = sys.stdout
        self._stderr = sys.stderr
        self._stringio = StringIO()
        sys.stdout = self._stringio
        sys.stderr = self._stringio
        self._excepthook = sys.excepthook
        sys.excepthook = sys.__excepthook__
        return self

    # This method gets called when we exit the managed context and here
    # we restore everything to the previous values to not interfere with Cura
    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio
        sys.stdout = self._stdout
        sys.stderr = self._stderr
        sys.excepthook = self._excepthook


# This class is our Extension and doubles as QObject to manage the qml, as
# well as the InteractiveInterpreter (this way we would be able to overwrite
# error output if we want, which we instead manage with our context manager)
class PythonConsole(QObject, Extension, InteractiveInterpreter):

    # The QT signal, which signals an update for the history text
    historyTextChanged = pyqtSignal()

    # The constructor, which calls all the super-class-contructors, registers
    # our menu items and initializes the internal instance variables
    def __init__(self, parent = None) -> None:
        QObject.__init__(self, parent)
        Extension.__init__(self)
        InteractiveInterpreter.__init__(self, globals())

        self.setMenuName(i18n_catalog.i18nc("@item:inmenu", "Python Console"))
        self.addMenuItem(i18n_catalog.i18nc("@item:inmenu", "Open Console"), self.showConsole)

        self._history = []
        self._console_window = None

    # This method gets called when the menu item for our plugin is clicked and
    # shows the console window if it has already been loaded
    def showConsole(self):
        if self._console_window is None:
            self._console_window = self._createDialogue()
        self._console_window.show()

    # Our QT slot, which reacts to the enter press in the text field and
    # executes the entered code. Here we use our context manager to redirect
    # output and prohibit Cura from crashing in the entered line of code.
    # When we finish executing the code we emit the QT signal, which signals an
    # update for the history text
    @pyqtSlot(str)
    def executeSourceLine(self, text):
        self._history.append('<font color="blue">&gt;&gt;&gt; '+html.escape(text)+'</font>')
        with ConsoleContextManager() as feedback:
            self.runsource(text)
        self._history.extend(map(lambda line: html.escape(line), feedback))
        self.historyTextChanged.emit()

    # Our QT property, which is computed on demand from our history list when
    # the appropriate signal is emitted
    @pyqtProperty(str, notify = historyTextChanged)
    def historyText(self):
        return "<br>".join(self._history)

    # This method builds our dialog from the qml file and registers this class
    # as the manager variable
    def _createDialogue(self):
        qml_file_path = os.path.join(PluginRegistry.getInstance().getPluginPath(self.getPluginId()), "ConsoleDialog.qml")
        component_with_context = Application.getInstance().createQmlComponent(qml_file_path, {"manager": self})
        return component_with_context
