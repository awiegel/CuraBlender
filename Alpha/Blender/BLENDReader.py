import sys
import platform
import os
import os.path
import glob
import random
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

        self._curasplit = False

        nodes = []
        temp_path = self._convertAndOpenFile(file_path, nodes)

        self._file_path = file_path
        #self._blender_path = Blender.blender_path

        self._changeWatchedFile(temp_path, file_path)

        if not self._curasplit:
            self._calculateAndSetScale(nodes)

        return nodes


    def _changeWatchedFile(self, old_path, new_path):
        Application.getInstance().getController().getScene().removeWatchedFile(old_path)
        Application.getInstance().getController().getScene().addWatchedFile(new_path)


    def _calculateAndSetScale(self, nodes):
        scale_factors = []
        for node in nodes:
            bounding_box = node.getBoundingBox()
            width = bounding_box.width
            height = bounding_box.height
            depth = bounding_box.depth

            message = None
            scale_factor = 1

            if((min(width, height, depth)) < 5):
                if not min(width, height, depth) == 0:
                    scale_factor = scale_factor * (5 / (scale_factor * min(width, height, depth)))
                    message = Message(text=i18n_catalog.i18nc('@info', 'Your object was too small and got scaled up to minimum print size'), title=i18n_catalog.i18nc('@info:title', 'Object was too small'))
            if(scale_factor * height) > 290:
                scale_factor = scale_factor * (290 / (scale_factor * height))
                message = Message(text=i18n_catalog.i18nc('@info', 'Your object was too high and got scaled down to maximum print size'), title=i18n_catalog.i18nc('@info:title', 'Object was too high'))

            if len(nodes) == 1:
                if((scale_factor * width) > 170) or ((scale_factor * depth) > 170):
                    scale_factor = scale_factor * (170 / (scale_factor * max(width, depth)))
                    message = Message(text=i18n_catalog.i18nc('@info', 'Your object was too broad and got scaled down to maximum print size'), title=i18n_catalog.i18nc('@info:title', 'Object was too broad'))
            elif len(nodes) <= 9:
                if((scale_factor * width) > (170 / 3)) or ((scale_factor * depth) > (170 / 3)):
                    scale_factor = scale_factor * ((170 / 3) / (scale_factor * max(width, depth)))
                    message = Message(text=i18n_catalog.i18nc('@info', 'Your objects were too broad together and got scaled down to maximum print size'), title=i18n_catalog.i18nc('@info:title', 'Objects were too broad'))
            elif len(nodes) <= 25:
                if((scale_factor * width) > (170 / 5)) or ((scale_factor * depth) > (170 / 5)):
                    scale_factor = scale_factor * ((170 / 5) / (scale_factor * max(width, depth)))
                    message = Message(text=i18n_catalog.i18nc('@info', 'Your objects were too broad together and got scaled down to maximum print size'), title=i18n_catalog.i18nc('@info:title', 'Objects were too broad'))
            elif len(nodes) <= 49:
                if((scale_factor * width) > (170 / 7)) or ((scale_factor * depth) > (170 / 7)):
                    scale_factor = scale_factor * ((170 / 7) / (scale_factor * max(width, depth)))
                    message = Message(text=i18n_catalog.i18nc('@info', 'Your objects were too broad together and got scaled down to maximum print size'), title=i18n_catalog.i18nc('@info:title', 'Objects were too broad'))
            elif len(nodes) <= 81:
                if((scale_factor * width) > (170 / 9)) or ((scale_factor * depth) > (170 / 9)):
                    scale_factor = scale_factor * ((170 / 9) / (scale_factor * max(width, depth)))
                    message = Message(text=i18n_catalog.i18nc('@info', 'Your objects were too broad together and got scaled down to maximum print size'), title=i18n_catalog.i18nc('@info:title', 'Objects were too broad'))
            else:
                None

            scale_factors.append(scale_factor)

        scale_factor = sum(scale_factors) / len(scale_factors)
        for node in nodes:
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
            command = self.buildCommand('Count nodes', file_path)
            objects = subprocess.run(command, shell = True, universal_newlines = True, stdout = subprocess.PIPE)
            for nextline in objects.stdout.splitlines():
                if nextline.isdigit():
                    objects = int(nextline)
                    break

            if objects <= 1:
                temp_path = self._buildTempPath(file_path)
                import_file = self._importFile(temp_path)
                command = self.buildCommand('Single node', file_path, import_file)
                subprocess.run(command, shell = True)

                node = self._openFile(temp_path)
                node.getMeshData()._file_name = file_path
                nodes.append(node)
            else:
                processes = []
                temp_paths = []
                for index in range(objects):
                    temp_path = self._buildTempPath(file_path, index)
                    import_file = self._importFile(temp_path)

                    command = self.buildCommand('Multiple nodes', file_path, import_file, str(index))
                    process = subprocess.Popen(command, shell = True)
                    processes.append(process)
                    temp_paths.append(temp_path)

                for (index, process, temp_path) in zip(range(objects), processes, temp_paths):
                    process.wait()
                    node = self._openFile(temp_path)
                    node.getMeshData()._file_name = '{}_curasplit_{}.blend'.format(file_path[:-6], index + 1)
                    nodes.append(node)

        else:
            self._curasplit = True
            index = int(file_path[file_path.index('_curasplit_') + 11:][:-6]) - 1
            file_path = '{}.blend'.format(file_path[:file_path.index('_curasplit_')])

            temp_path = self._buildTempPath(file_path, index + 1)
            import_file = self._importFile(temp_path)

            command = self.buildCommand('Multiple nodes', file_path, import_file, str(index))
            subprocess.run(command, shell = True)

            node = self._openFile(temp_path)
            node.getMeshData()._file_name = '{}_curasplit_{}.blend'.format(file_path[:-6], index + 1)
            nodes.append(node)

        return temp_path


    def _buildTempPath(self, file_path, index = None):
        if index:
            # temp_path = '{}/cura_temp_{}_{}.{}'.format(os.path.dirname(file_path), os.path.basename(file_path).rsplit('.', 1)[0], index, Blender.file_extension)
            temp_path = '{}/cura_temp_{}_{}.{}'.format(os.path.dirname(file_path), str(random.random())[2:], index, Blender.file_extension)
        else:
            # temp_path = '{}/cura_temp_{}.{}'.format(os.path.dirname(file_path), os.path.basename(file_path).rsplit('.', 1)[0], Blender.file_extension)
            temp_path = '{}/cura_temp_{}.{}'.format(os.path.dirname(file_path), str(random.random())[2:], Blender.file_extension)

        return temp_path

    @classmethod
    def buildCommand(self, program, file_path, instruction = None, index = None, background = True):
        if not 'self._script_path' in locals():
            self._script_path = '{}/plugins/Blender/BlenderAPI.py'.format(os.getcwd())

        if program == 'Count nodes' or program == 'Single node':
            command = (
                Blender.blender_path,
                file_path,
                '--background',
                '--python',
                self._script_path,
                '--', program
            )
            if instruction:
                command = command[:-1] + (instruction,) + command[-1:]
        else:
            command = (
                Blender.blender_path,
                '--background',
                '--python',
                self._script_path,
                '--', instruction, index, file_path, program
            )
            #command = command[:-2] + (instruction,) + (index,) + command[-2:]

        if not background:
            command = command[:1] + command[2:]

        # if instruction and not index:
        #     command = command[:-2] + (instruction,) + command[-2:]
        # elif index:
        #     command = command[:-2] + (instruction,) + (index,) + command[-2:]
        # else:
        #     None

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


    def _openFile(self, temp_path):
        reader = Application.getInstance().getMeshFileHandler().getReaderForFile(temp_path)
        try:
            node = reader.read(temp_path)
            os.remove(temp_path)
        except:
            Logger.logException('e', 'Could not read file')
            os.remove(temp_path)
        return node
