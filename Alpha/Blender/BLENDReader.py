import sys
import platform
import os.path
import glob
import subprocess

from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import QTimer, QUrl
from PyQt5.QtGui import QDesktopServices

from UM.Logger import Logger
from UM.Message import Message
from UM.Application import Application
from UM.Mesh.MeshReader import MeshReader
from UM.Math.Vector import Vector
from UM.i18n import i18nCatalog

i18n_catalog = i18nCatalog('uranium')

global global_path, blender_path, message_flag, file_extension
global_path = None
blender_path = None
message_flag = None
file_extension = 'stl'

class BLENDReader(MeshReader):
    def __init__(self) -> None:
        super().__init__()
        self._supported_extensions = ['.blend']


    # Main entry point
    # Reads the file, returns a SceneNode (possibly with nested ones), or None
    def read(self, file_path):
        global global_path, blender_path
        system = platform.system()

        if not blender_path:
            blender_path = self._setBlenderPath(blender_path, system)
        
        if not os.path.exists(blender_path):
            blender_path = self._openFileDialog(blender_path, system)

        global_path = file_path
        temp_path = self._convertFile(blender_path, file_path)
        data = self._openFile(temp_path)

        data.getMeshData()._file_name = file_path
        Application.getInstance().getController().getScene().removeWatchedFile(temp_path)
        Application.getInstance().getController().getScene().addWatchedFile(file_path)

        self._calculateAndSetScale(data)
        return data


    def _calculateAndSetScale(self, node):
        global message_flag
        bounding_box = node.getBoundingBox()
        width = bounding_box.width
        height = bounding_box.height
        depth = bounding_box.depth

        scale_factor = 1
        message = None

        if((min(width, height, depth)) < 5):
            if not min(width, height, depth) == 0:
                scale_factor = scale_factor * (5 / (scale_factor * min(width, height, depth)))
                message = Message(text=i18n_catalog.i18nc('@info', 'Your object was too small and got scaled up to minimum print size'), title=i18n_catalog.i18nc('@info:title', 'Object was too small'))
        if((scale_factor * height) > 290):
            scale_factor = scale_factor * (290 / (scale_factor * height))
            message = Message(text=i18n_catalog.i18nc('@info', 'Your object was too high and got scaled down to maximum print size'), title=i18n_catalog.i18nc('@info:title', 'Object was too high'))
        if((scale_factor * width) > 170 or (scale_factor * depth) > 170):
            scale_factor = scale_factor * (170 / (scale_factor * max(width, depth)))
            message = Message(text=i18n_catalog.i18nc('@info', 'Your object was too broad and got scaled down to maximum print size'), title=i18n_catalog.i18nc('@info:title', 'Object was too broad'))
        
        if message:
            message.addAction('Open in Blender', i18n_catalog.i18nc('@action:button', 'Open in Blender'),
                          '[no_icon]', '[no_description]', button_align=Message.ActionButtonAlignment.ALIGN_LEFT)
            message.addAction('Ignore', i18n_catalog.i18nc('@action:button', 'Ignore'),
                          '[no_icon]', '[no_description]', button_style=Message.ActionButtonStyle.SECONDARY, button_align=Message.ActionButtonAlignment.ALIGN_RIGHT)
            message.actionTriggered.connect(self._openBlenderTrigger)
            if not message_flag:
                message.show()
            message_flag = None

        node.scale(scale = Vector(scale_factor,scale_factor,scale_factor))


    def _openBlenderTrigger(self, message, action):
        if action == 'Open in Blender':
            if blender_path is None:
                QDesktopServices.openUrl(QUrl('https://www.blender.org/download/'))
            elif global_path is None:
                subprocess.Popen(blender_path, shell = True)
            else:
                subprocess.Popen((blender_path, global_path), shell = True)
        elif action == 'Ignore':
            message.hide()


    def _setBlenderPath(self, blender_path, system):
        if system == 'Windows':
            temp_blender_path = glob.glob('C:/Program Files/Blender Foundation/**/*.exe')
            blender_path = ''.join(temp_blender_path).replace('\\', '/')
            #blender_path = 'test'
        elif system == 'Darwin':
            blender_path = '/Applications/Blender.app/Contents/MacOS/blender'
        elif system == 'Linux':
            blender_path = '/usr/share/blender/2.82/blender'
        else:
            blender_path = None
        return blender_path


    def _openFileDialog(self, blender_path, system):
        message = Message(text=i18n_catalog.i18nc('@info', 'Set your blender path manually'), title=i18n_catalog.i18nc('@info:title', 'Blender not found'))
        message.show()

        dialog = QFileDialog()
        dialog.setAcceptMode(QFileDialog.AcceptOpen)
        if system == 'Windows':
            dialog.setDirectory('C:/Program Files')
            dialog.setNameFilters(["Blender (*.exe)"])
        elif system == 'Darwin':
            dialog.setDirectory('/Applications')
            dialog.setNameFilters(["Blender (*.app)"])
        elif system == 'Linux':
            dialog.setDirectory('/usr/share')
        else:
            dialog.setDirectory('')

        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setViewMode(QFileDialog.Detail)
        if dialog.exec_():
            message.hide()
        blender_path = ''.join(dialog.selectedFiles())
        return blender_path


    def _convertFile(self, blender_path, file_path):
        #global file_extension
        temp_path = '{}/temp.{}'.format(os.path.dirname(file_path), file_extension)
        if file_extension == 'stl' or file_extension == 'ply':
            export = 'bpy.ops.export_mesh.{}(filepath = "{}", check_existing = False)'.format(file_extension, temp_path)
        elif file_extension == 'obj' or file_extension == 'x3d':
            export = 'bpy.ops.export_scene.{}(filepath = "{}", check_existing = False)'.format(file_extension, temp_path)

        command = (
            blender_path,
            file_path,
            '--background',
            '--python-expr',
            'import bpy;'
            'import sys;'
            'exec(sys.argv[-1])',
            '--', export
        )

        subprocess.run(command, shell = True)
        return temp_path


    def _openFile(self, temp_path):
        reader = Application.getInstance().getMeshFileHandler().getReaderForFile(temp_path)
        data = reader.read(temp_path)
        os.remove(temp_path)
        return data
