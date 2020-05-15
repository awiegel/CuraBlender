from UM.Extension import Extension
from UM.i18n import i18nCatalog
from UM.Logger import Logger
from UM.Message import Message

i18n_catalog = i18nCatalog("uranium")


class Blender(Extension):
    def __init__(self):
        super().__init__()
        self.setMenuName(i18n_catalog.i18nc("@item:inmenu", "Blender"))
        self.addMenuItem(i18n_catalog.i18nc("@item:inmenu", "Select Blender File"), self.openFile)

    def openFile(self):
        Logger.log("e", "Not opening file since this feature is currently under development.")
        Message(i18n_catalog.i18nc("@info", "Feature not implemented yet."),
                title=i18n_catalog.i18nc("@info:title", "Work in Progress")).show()
        #self.filename = filedialog.askopenfilename(initialdir="/", title="Select Blender File", filetype=("blend", "*.blend"))
        return
