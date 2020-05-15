from UM.Extension import Extension
from UM.i18n import i18nCatalog
from UM.Logger import Logger
from UM.Message import Message

from PyQt5.QtCore import QTimer, QUrl
from PyQt5.QtGui import QDesktopServices

i18n_catalog = i18nCatalog("uranium")


class Blender(Extension):
    def __init__(self):
        super().__init__()
        self.setMenuName(i18n_catalog.i18nc("@item:inmenu", "Blender"))
        self.addMenuItem(i18n_catalog.i18nc("@item:inmenu", "Select Blender File"), self.openFile)
        self.addMenuItem(i18n_catalog.i18nc("@item:inmenu", "Scale Size"), self.scaleSize)
        self.addMenuItem(i18n_catalog.i18nc("@item:inmenu", "Check Waterproof"), self.checkWaterproof)
        self.addMenuItem(i18n_catalog.i18nc("@item:inmenu", "Reload Object"), self.reloadFile)

    def getMessage(self, title, text):
        message = Message(text=i18n_catalog.i18nc("@info", text), title=i18n_catalog.i18nc("@info:title", title))
        return message

    def openFile(self):
        Logger.log("i", "Select Blender File is currently under development.")
        message = self.getMessage("Work in Progress", "Select Blender File is not implemented yet.")
        message.show()

    def scaleSize(self):
        Logger.log("i", "Scale Size is currently under development.")
        message = self.getMessage("Work in Progress", "Scale Size is not implemented yet.")
        message.show()

    def checkWaterproof(self):
        Logger.log("i", "Check Waterproof is currently under development.")
        message = self.getMessage("Check Waterproof!", "Your Object is not waterproof! You can fix it directly in Blender ;)")
        message.addAction("Open in Blender", i18n_catalog.i18nc("@action:button", "Open in Blender"),
                          "[no_icon]", "[no_description]", button_align=Message.ActionButtonAlignment.ALIGN_LEFT)
        message.addAction("Ignore", i18n_catalog.i18nc("@action:button", "Ignore"),
                          "[no_icon]", "[no_description]", button_style=Message.ActionButtonStyle.SECONDARY, button_align=Message.ActionButtonAlignment.ALIGN_RIGHT)
        message.actionTriggered.connect(self._onActionTriggered)
        message.show()

    def reloadFile(self):
        Logger.log("i", "Reload File is currently under development.")
        message = self.getMessage("Work in Progress", "Reload Object is not implemented yet.")
        message.show()

    def _onActionTriggered(self, message, action):
        """Callback function for the "download" button on the update notification.

        This function is here is because the custom Signal in Uranium keeps a list of weak references to its
        connections, so the callback functions need to be long-lived. The Blender is short-lived so
        this function cannot be there.
        """
        if action == "Open in Blender":
            QDesktopServices.openUrl(QUrl("https://www.blender.org/download/"))
        elif action == "Ignore":
            message.hide()
