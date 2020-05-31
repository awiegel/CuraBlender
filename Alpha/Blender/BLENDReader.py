import sys
import platform
import os.path
import os
import glob
import subprocess
from subprocess import PIPE

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


    # Main entry point
    # Reads the file, returns a SceneNode (possibly with nested ones), or None
    def read(self, file_path):
        if not Blender.blender_path:
            Blender.Blender.setBlenderPath()

        nodes = []
        temp_path = self._convertAndOpenFile(file_path, nodes)

        self._file_path = file_path
        #self._blender_path = Blender.blender_path

        self._changeWatchedFile(temp_path, file_path)

        self._calculateAndSetScale(nodes)

        return nodes

    def _changeWatchedFile(self, old_path, new_path):
        Application.getInstance().getController().getScene().removeWatchedFile(old_path)
        Application.getInstance().getController().getScene().addWatchedFile(new_path)


    def _calculateAndSetScale(self, nodes):
        for node in nodes:
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
            if(scale_factor * height) > (290 / len(nodes)):
                scale_factor = scale_factor * ((290 / len(nodes)) / (scale_factor * height))
                message = Message(text=i18n_catalog.i18nc('@info', 'Your object was too high and got scaled down to maximum print size'), title=i18n_catalog.i18nc('@info:title', 'Object was too high'))
            if((scale_factor * width) > (170 / len(nodes))) or ((scale_factor * depth) > (170 / len(nodes))):
                scale_factor = scale_factor * ((170 / len(nodes)) / (scale_factor * max(width, depth)))
                message = Message(text=i18n_catalog.i18nc('@info', 'Your object was too broad and got scaled down to maximum print size'), title=i18n_catalog.i18nc('@info:title', 'Object was too broad'))
        
            node.scale(scale = Vector(scale_factor,scale_factor,scale_factor))

        if message:
            message._lifetime = 10
            message.addAction('Open in Blender', i18n_catalog.i18nc('@action:button', 'Open in Blender'),
                          '[no_icon]', '[no_description]', button_align=Message.ActionButtonAlignment.ALIGN_LEFT)
            message.addAction('Ignore', i18n_catalog.i18nc('@action:button', 'Ignore'),
                          '[no_icon]', '[no_description]', button_style=Message.ActionButtonStyle.SECONDARY, button_align=Message.ActionButtonAlignment.ALIGN_RIGHT)
            message.actionTriggered.connect(self._openBlenderTrigger)
            message.show()


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
        else:
            None


    def _convertAndOpenFile(self, file_path, nodes):
        if '_curasplit_' not in file_path:

            command = self.buildCommand(file_path, 'Count nodes')
            objects = subprocess.run(command, shell = True, universal_newlines = True, stdout = subprocess.PIPE)
            objects = int(objects.stdout.splitlines()[4])

            temp_path = '{}/cura_temp.{}'.format(os.path.dirname(file_path), Blender.file_extension)
            import_file = self._importFile(temp_path)

            if objects <= 1:
                command = self.buildCommand(file_path, 'Single node', import_file)
                subprocess.run(command, shell = True)

                node = self._openFile(temp_path, nodes)

                node.getMeshData()._file_name = file_path
                nodes.append(node)
            else:
                for node in range(objects):
                    index = str(node)

                    command = self.buildCommand(file_path, 'Multiple nodes', import_file, index)
                    subprocess.run(command, shell = True)

                    node = self._openFile(temp_path, nodes)
                    node.getMeshData()._file_name = '{}_curasplit_{}.blend'.format(file_path[:-6], int(index) + 1)
                    nodes.append(node)

        else:
            index = int(file_path[file_path.index('_curasplit_') + 11:][:-6]) - 1
            file_path = '{}.blend'.format(file_path[:file_path.index('_curasplit_')])

            temp_path = '{}/cura_temp_{}.{}'.format(os.path.dirname(file_path), index + 1, Blender.file_extension)
            import_file = self._importFile(temp_path)

            command = self.buildCommand(file_path, 'Multiple nodes', import_file, str(index))
            subprocess.run(command, shell = True)

            node = self._openFile(temp_path, nodes)
            node.getMeshData()._file_name = '{}_curasplit_{}.blend'.format(file_path[:-6], index + 1)
            nodes.append(node)

        return temp_path


    @classmethod
    def buildCommand(self, file_path, program, instruction = None, index = None, background = True):
        if not 'self._script_path' in locals():
            self._script_path = '{}/plugins/Blender/BlenderAPI.py'.format(os.getcwd())

        if background == True:
            command = (
                Blender.blender_path,
                file_path,
                '--background',
                '--python',
                self._script_path,
                '--', program
            )
        else:
            command = (
                Blender.blender_path,
                file_path,
                '--python',
                self._script_path,
                '--', program
            )

        if instruction and not index:
            command = command[:-1] + (instruction,) + command[-1:]
        elif index:
            command = command[:-1] + (instruction,) + (index,) + command[-1:]
        else:
            None

        return command


    def _importFile(self, file_path):
        if Blender.file_extension == 'stl' or Blender.file_extension == 'ply':
            import_file = 'bpy.ops.export_mesh.{}(filepath = "{}", check_existing = False)'.format(Blender.file_extension, file_path)
        elif Blender.file_extension == 'obj' or Blender.file_extension == 'x3d':
            import_file = 'bpy.ops.export_scene.{}(filepath = "{}", check_existing = False)'.format(Blender.file_extension, file_path)
        else:
            import_file = None
            Logger.logException('e', '%s is not supported!', Blender.file_extension)
        return import_file


    def _openFile(self, temp_path, nodes):
        reader = Application.getInstance().getMeshFileHandler().getReaderForFile(temp_path)
        node = reader.read(temp_path)
        os.remove(temp_path)
        return node
