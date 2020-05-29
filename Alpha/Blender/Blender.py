import subprocess

from UM.Logger import Logger
from UM.Message import Message
from UM.Extension import Extension
from UM.Application import Application
from UM.i18n import i18nCatalog

from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices

from . import BLENDReader

#from UM.Operations.GroupedOperation import GroupedOperation
#from UM.Scene.Selection import Selection
from UM.Scene.SceneNode import SceneNode
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
#from UM.Operations.RemoveSceneNodeOperation import RemoveSceneNodeOperation
#from UM.Operations.AddSceneNodeOperation import AddSceneNodeOperation

from UM.Math.Vector import Vector
from cura.Scene.CuraSceneNode import CuraSceneNode

# from PyQt5.QtCore import QFileSystemWatcher  # To watch files for changes.
#from PyQt5 import QtCore
# from UM.Signal import Signal, signalemitter
#from PyQt5.QtCore import Signal

i18n_catalog = i18nCatalog('uranium')

# @signalemitter
class Blender(Extension):
    def __init__(self):
        super().__init__()
        self._supported_extensions = ['.blend']
        self._namespaces = {}   # type: Dict[str, str]
        self.setMenuName(i18n_catalog.i18nc('@item:inmenu', 'Blender'))
        self.addMenuItem(i18n_catalog.i18nc('@item:inmenu', 'Open in Blender'), self.openInBlender)
        self.addMenuItem(i18n_catalog.i18nc('@item:inmenu', 'Scale Size'), self.scaleSize)
        self.addMenuItem(i18n_catalog.i18nc('@item:inmenu', 'Check Waterproof'), self.checkWaterproof)
        self.addMenuItem(i18n_catalog.i18nc('@item:inmenu', 'Reload Object'), self.reloadFile)
        self.addMenuItem(i18n_catalog.i18nc('@item:inmenu', 'File Extension'), self.file_extension)

        #BLENDReader.global_path = None
        #BLENDReader.blender_path = None


    def getMessage(self, title, text):
        message = Message(text=i18n_catalog.i18nc('@info', text), title=i18n_catalog.i18nc('@info:title', title))
        return message


    def openInBlender(self):
        if BLENDReader.blender_path is None:
            QDesktopServices.openUrl(QUrl('https://www.blender.org/download/'))
        elif BLENDReader.global_path is None:
            subprocess.Popen(BLENDReader.blender_path, shell = True)
        else:
            subprocess.Popen((BLENDReader.blender_path, BLENDReader.global_path), shell = True)

    def file_extension(self):
        message = self.getMessage('File Extension', 'Choose your File Extension.')
        message.addAction('stl', i18n_catalog.i18nc('@action:button', 'stl'),
                          '[no_icon]', '[no_description]')
        message.addAction('ply', i18n_catalog.i18nc('@action:button', 'ply'),
                          '[no_icon]', '[no_description]')
        message.addAction('x3d', i18n_catalog.i18nc('@action:button', 'x3d'),
                          '[no_icon]', '[no_description]')
        message.addAction('obj', i18n_catalog.i18nc('@action:button', 'obj'),
                          '[no_icon]', '[no_description]')
        message.actionTriggered.connect(self._fileExtensionTrigger)
        message.show()


    def _fileExtensionTrigger(self, message, action):
        if action == 'stl':
            BLENDReader.file_extension = 'stl'
        elif action == 'ply':
            BLENDReader.file_extension = 'ply'
        elif action == 'x3d':
            BLENDReader.file_extension = 'x3d'
        elif action == 'obj':
            BLENDReader.file_extension = 'obj'


    def scaleSize(self):
        Logger.log('i', 'Scale Size is currently under development.')
        message = self.getMessage('Scale Size', 'Choose your Size.')
        message.addAction('MAXIMUM', i18n_catalog.i18nc('@action:button', 'MAXIMUM'),
                          '[no_icon]', '[no_description]')
        message.addAction('AVERAGE', i18n_catalog.i18nc('@action:button', 'AVERAGE'),
                          '[no_icon]', '[no_description]', button_style=Message.ActionButtonStyle.SECONDARY)
        message.addAction('MINIMUM', i18n_catalog.i18nc('@action:button', 'MINIMUM'),
                          '[no_icon]', '[no_description]')
        message.actionTriggered.connect(self._scaleTrigger)
        message.show()


    def _scaleTrigger(self, message, action):
        '''Callback function for the 'download' button on the update notification.

        This function is here is because the custom Signal in Uranium keeps a list of weak references to its
        connections, so the callback functions need to be long-lived. The Blender is short-lived so
        this function cannot be there.
        '''
        if action == 'MAXIMUM':
            for node in DepthFirstIterator(Application.getInstance().getController().getScene().getRoot()):
                if isinstance(node, CuraSceneNode):
                    Logger.log('d', node.getParent().getBoundingBox())
                    self.calculateAndSetScale(node, 290)
        elif action == 'AVERAGE':
            for node in DepthFirstIterator(Application.getInstance().getController().getScene().getRoot()):
                if isinstance(node, CuraSceneNode):
                    self.calculateAndSetScale(node, 100)
        elif action == 'MINIMUM':
            for node in DepthFirstIterator(Application.getInstance().getController().getScene().getRoot()):
                if isinstance(node, CuraSceneNode):
                    self.calculateAndSetScale(node, 5)


    def calculateAndSetScale(self, node, size):
        bounding_box = node.getBoundingBox()
        width = bounding_box.width
        height = bounding_box.height
        depth = bounding_box.depth

        scale_factor = (size / max(width, height, depth))

        if((scale_factor * min(width, height, depth)) < 5):
            if not min(width, height, depth) == 0:
                scale_factor = scale_factor * (5 / (scale_factor * min(width, height, depth)))
        if((scale_factor * height) > 290):
            scale_factor = scale_factor * (290 / (scale_factor * height))
        if((scale_factor * width) > 170 or (scale_factor * depth) > 170):
            scale_factor = scale_factor * (170 / (scale_factor * max(width, depth)))

        node.scale(scale = Vector(scale_factor,scale_factor,scale_factor))

        if not Vector(scale_factor,scale_factor,scale_factor) == Vector(1,1,1):
            Logger.log('i', 'Scaling Node with factor %s', scale_factor)
            Logger.log('i', 'Before: (width: %s, height: %s, depth: %s', width, height, depth)
            Logger.log('i', 'After: (width: %s, height: %s, depth: %s', (width * scale_factor), (height * scale_factor), (depth * scale_factor))


    #@pyqtSlot()
    def reloadFile(self):
        Logger.log('i', 'File Reloaded - Ready for F5')
        message = self.getMessage('Reloaded File', 'Press F5 to reload your file.')
        message.show()
#        Logger.log("i", "Clearing scene")
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
        BLENDReader.message_flag = True
        BLENDReader.BLENDReader.read(BLENDReader.BLENDReader(), BLENDReader.global_path)


    def checkWaterproof(self):
        Logger.log('i', 'Check Waterproof is currently under development.')
        message = self.getMessage('Check Waterproof!', 'Your Object is not waterproof! You can fix it directly in Blender ;)')
        message.addAction('Open in Blender', i18n_catalog.i18nc('@action:button', 'Open in Blender'),
                          '[no_icon]', '[no_description]', button_align=Message.ActionButtonAlignment.ALIGN_LEFT)
        message.addAction('Ignore', i18n_catalog.i18nc('@action:button', 'Ignore'),
                          '[no_icon]', '[no_description]', button_style=Message.ActionButtonStyle.SECONDARY, button_align=Message.ActionButtonAlignment.ALIGN_RIGHT)
        message.addAction('TEST', i18n_catalog.i18nc('@action:button', 'TEST'),
                          '[no_icon]', '[no_description]')
        message.actionTriggered.connect(self._waterproofTrigger)
        message.show()


    def _waterproofTrigger(self, message, action):
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
        elif action == 'TEST':
            Logger.log('d', 'TESTTEST')
            # fs_watcher = QFileSystemWatcher()
            # #fs_watcher.fileChanged.connect(fs_watcher, QtCore.Signal('fileChanged(QString)'), self.file_changed)
            # fs_watcher.fileChanged.connect(self.file_changed)
            # fs_watcher.addPath(BLENDReader.global_path)
            # Logger.log('d', fs_watcher)


    # #@QtCore.pyqtSlot(str)
    # def file_changed(self, path):
    #     Logger.log('d', 'FILE CHANGE TEST')
