import subprocess

from UM.Extension import Extension
from UM.Application import Application
from UM.i18n import i18nCatalog
from UM.Logger import Logger
from UM.Message import Message

from PyQt5.QtCore import QTimer, QUrl
from PyQt5.QtGui import QDesktopServices

from . import BLENDReader

from UM.Operations.GroupedOperation import GroupedOperation
from UM.Scene.Selection import Selection
from UM.Scene.SceneNode import SceneNode
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Operations.RemoveSceneNodeOperation import RemoveSceneNodeOperation
from UM.Operations.AddSceneNodeOperation import AddSceneNodeOperation

i18n_catalog = i18nCatalog('uranium')


from UM.FileHandler.ReadFileJob import ReadFileJob
from UM.Qt.QtApplication import QtApplication

class Blender(Extension):
    def __init__(self):
        super().__init__()
        self._supported_extensions = ['.blend']
        self._namespaces = {}   # type: Dict[str, str]
        self.setMenuName(i18n_catalog.i18nc('@item:inmenu', 'Blender'))
        self.addMenuItem(i18n_catalog.i18nc('@item:inmenu', 'Scale Size'), self.scaleSize)
        self.addMenuItem(i18n_catalog.i18nc('@item:inmenu', 'Check Waterproof'), self.checkWaterproof)
        self.addMenuItem(i18n_catalog.i18nc('@item:inmenu', 'Reload Object'), self.reloadFile)

        BLENDReader.global_path = None
        BLENDReader.blender_path = None

    def getMessage(self, title, text):
        message = Message(text=i18n_catalog.i18nc('@info', text), title=i18n_catalog.i18nc('@info:title', title))
        return message

    def scaleSize(self):
        Logger.log('i', 'Scale Size is currently under development.')
        message = self.getMessage('Work in Progress', 'Scale Size is not implemented yet.')
        message.show()

    def checkWaterproof(self):
        Logger.log('i', 'Check Waterproof is currently under development.')
        message = self.getMessage('Check Waterproof!', 'Your Object is not waterproof! You can fix it directly in Blender ;)')
        message.addAction('Open in Blender', i18n_catalog.i18nc('@action:button', 'Open in Blender'),
                          '[no_icon]', '[no_description]', button_align=Message.ActionButtonAlignment.ALIGN_LEFT)
        message.addAction('Ignore', i18n_catalog.i18nc('@action:button', 'Ignore'),
                          '[no_icon]', '[no_description]', button_style=Message.ActionButtonStyle.SECONDARY, button_align=Message.ActionButtonAlignment.ALIGN_RIGHT)
        message.actionTriggered.connect(self._onActionTriggered)
        message.show()


    def reloadFile(self):
        Logger.log('i', 'Reload File is currently under development.')
        message = self.getMessage('Work in Progress', 'Reload Object is not implemented yet.')
        message.show()
        Logger.log("i", "Clearing scene")
#        scene = Application.getInstance().getController().getScene()
#        nodes = []
#        new_node = BLENDReader.BLENDReader.read(BLENDReader.BLENDReader(), BLENDReader.global_path)

#        new_node.setSelectable(True)
        
#        for node in DepthFirstIterator(scene.getRoot()):
#            if not node.isEnabled():
#                continue
#            if not node.getMeshData() and not node.callDecoration("isGroup"):
#                continue  # Node that doesnt have a mesh and is not a group.
            #if only_selectable and not node.isSelectable():
            #    continue  # Only remove nodes that are selectable.
            #if node.getParent() and cast(SceneNode, node.getParent()).callDecoration("isGroup"):
            #    continue  # Grouped nodes don't need resetting as their parent (the group) is resetted)
#            nodes.append(node)
#        if nodes:
            #from UM.Operations.GroupedOperation import GroupedOperation
#            op = GroupedOperation()

#            for node in nodes:
                #from UM.Operations.RemoveSceneNodeOperation import RemoveSceneNodeOperation
#                op.addOperation(RemoveSceneNodeOperation(node))
#                op.addOperation(AddSceneNodeOperation(new_node, scene.getRoot()))

                # Reset the print information
#                scene.sceneChanged.emit(node)

#            op.push()
            #from UM.Scene.Selection import Selection
#            Selection.clear()
        BLENDReader.BLENDReader.read(BLENDReader.BLENDReader(), BLENDReader.global_path)
        Logger.log('d', 'TESTTEST')

    def _onActionTriggered(self, message, action):
        '''Callback function for the 'download' button on the update notification.

        This function is here is because the custom Signal in Uranium keeps a list of weak references to its
        connections, so the callback functions need to be long-lived. The Blender is short-lived so
        this function cannot be there.
        '''
        if action == 'Open in Blender':
            if BLENDReader.blender_path is None:
                QDesktopServices.openUrl(QUrl('https://www.blender.org/download/'))
            elif BLENDReader.global_path is None:
                subprocess.Popen(BLENDReader.blender_path, shell = True)
            else:
                subprocess.Popen((BLENDReader.blender_path, BLENDReader.global_path), shell = True)
        elif action == 'Ignore':
            message.hide()
