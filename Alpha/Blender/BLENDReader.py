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

from . import Blender


class BLENDReader(MeshReader):
    def __init__(self) -> None:
        super().__init__()
        self._supported_extensions = ['.blend']
        if not Blender.blender_path:
            Blender.Blender.setBlenderPath()
        #self._file_path = None

    # Main entry point
    # Reads the file, returns a SceneNode (possibly with nested ones), or None
    def read(self, file_path):
        temp_path = self._convertFile(file_path)
        data = self._openFile(temp_path)

        data.getMeshData()._file_name = file_path

        self._file_path = file_path
        #self._blender_path = Blender.blender_path

        self._changeWatchedFile(temp_path, file_path)

        self._calculateAndSetScale(data)

        return data

    def _changeWatchedFile(self, old_path, new_path):
        Application.getInstance().getController().getScene().removeWatchedFile(old_path)
        Application.getInstance().getController().getScene().addWatchedFile(new_path)


    def _calculateAndSetScale(self, node):
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
            message._lifetime = 10
            message.addAction('Open in Blender', i18n_catalog.i18nc('@action:button', 'Open in Blender'),
                          '[no_icon]', '[no_description]', button_align=Message.ActionButtonAlignment.ALIGN_LEFT)
            message.addAction('Ignore', i18n_catalog.i18nc('@action:button', 'Ignore'),
                          '[no_icon]', '[no_description]', button_style=Message.ActionButtonStyle.SECONDARY, button_align=Message.ActionButtonAlignment.ALIGN_RIGHT)
            message.actionTriggered.connect(self._openBlenderTrigger)
            message.show()

        node.scale(scale = Vector(scale_factor,scale_factor,scale_factor))


    def _openBlenderTrigger(self, message, action):
        if action == 'Open in Blender':
            if Blender.blender_path is None:
                QDesktopServices.openUrl(QUrl('https://www.blender.org/download/'))
            elif self._file_path is None:
                subprocess.run(Blender.blender_path, shell = True)
            else:
                subprocess.run((Blender.blender_path, self._file_path), shell = True)
        elif action == 'Ignore':
            message.hide()


    def _convertFile(self, file_path):  
        temp_path = '{}/cura_temp.{}'.format(os.path.dirname(file_path), Blender.file_extension)
        import_file = self._importFile(temp_path)

        command = (
            Blender.blender_path,
            file_path,
            '--background',
            '--python-expr',
            'import bpy;'
            'import sys;'
            'exec(sys.argv[-1])',
            '--', import_file
        )

        subprocess.run(command, shell = True)
        return temp_path


    def _importFile(self, file_path):
        if Blender.file_extension == 'stl' or Blender.file_extension == 'ply':
            import_file = 'bpy.ops.export_mesh.{}(filepath = "{}", check_existing = False)'.format(Blender.file_extension, file_path)
        elif Blender.file_extension == 'obj' or Blender.file_extension == 'x3d':
            import_file = 'bpy.ops.export_scene.{}(filepath = "{}", check_existing = False)'.format(Blender.file_extension, file_path)
        else:
            import_file = None
            Logger.logException('e', '%s is not supported!', Blender.file_extension)
        return import_file


    def _openFile(self, temp_path):
        reader = Application.getInstance().getMeshFileHandler().getReaderForFile(temp_path)
        data = reader.read(temp_path)
        os.remove(temp_path)
        return data
