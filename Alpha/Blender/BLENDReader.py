# Imports from the python standard library.
import os
import random
import subprocess
from subprocess import PIPE

# Imports from QT.
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices

# Imports from Uranium.
from UM.Mesh.MeshReader import MeshReader
from UM.Logger import Logger
from UM.Message import Message
from UM.Application import Application
from UM.Math.Vector import Vector
from UM.i18n import i18nCatalog
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator

# Imports from Cura.
from cura.Scene.CuraSceneNode import CuraSceneNode

# Imports from own package.
from . import Blender


# The catalog used for showing messages.
i18n_catalog = i18nCatalog('uranium')


##  Reader class for .blend files.
class BLENDReader(MeshReader):
    ##  The constructor, which calls the super-class-contructor (MeshReader).
    ##  Adds .blend as a supported file extension.
    def __init__(self) -> None:
        super().__init__()
        self._supported_extensions = ['.blend']


    ##  Main entry point for reading the file.
    #
    #   \param file_path  The path of the file we try to open.
    #   \return           A list of all nodes contained in the file.
    def read(self, file_path):
        # Checks if path for blender is set, otherwise tries to set it.
        if not Blender.blender_path:
            Blender.Blender.setBlenderPath()

        nodes = []
        if Blender.blender_path:
            self._curasplit = False

            temp_path = self._convertAndOpenFile(file_path, nodes)

            if temp_path:
                self._file_path = file_path

                self._changeWatchedFile(temp_path, file_path)

                if not self._curasplit:
                    for node in DepthFirstIterator(Application.getInstance().getController().getScene().getRoot()):
                        if isinstance(node, CuraSceneNode):
                            # Checks if read is actually a reload or if the file is already opened and suppress the scaling message.
                            if file_path in node.getMeshData().getFileName() or file_path[:-6] + '_curasplit_' in node.getMeshData().getFileName():
                                self._curasplit = True
                                break

                self._calculateAndSetScale(nodes)
            else:
                message = Message(text=i18n_catalog.i18nc('@info', 'Your file did not contain any objects.'), title=i18n_catalog.i18nc('@info:title', 'No object found'))
                message.show()

        return nodes


    # After reading exported file change file reference to .blend clone
    def _changeWatchedFile(self, old_path, new_path):
        Application.getInstance().getController().getScene().removeWatchedFile(old_path)
        Blender.fs_watcher.addPath(new_path)


    # Reads all nodes contained in the file
    # Calculates the needed scale factor based on equivalence classes and finally scales all nodes equally
    def _calculateAndSetScale(self, nodes):
        # Checks auto scale flag in settings file.
        if Blender.Blender.loadJsonFile('auto_scale'):
            scale_factors = []
            for node in nodes:
                bounding_box = node.getBoundingBox()
                width = bounding_box.width
                height = bounding_box.height
                depth = bounding_box.depth

                message = None
                scale_factor = 1

                # Checks the minimum size of the object
                if((min(width, height, depth)) < 5):
                    if not min(width, height, depth) == 0:
                        scale_factor = scale_factor * (5 / (scale_factor * min(width, height, depth)))
                        message = Message(text=i18n_catalog.i18nc('@info', 'Your object was too small and got scaled up to minimum print size'), title=i18n_catalog.i18nc('@info:title', 'Object was too small'))
                # Checks the maximum height of the object
                if(scale_factor * height) > 290:
                    scale_factor = scale_factor * (290 / (scale_factor * height))
                    message = Message(text=i18n_catalog.i18nc('@info', 'Your object was too high and got scaled down to maximum print size'), title=i18n_catalog.i18nc('@info:title', 'Object was too high'))

                # Checks the maximum width/depth based on number of objects, because cura doesn't allow to manipulate the position of the object.
                # The first object gets loaded exactly in the middle and every other object will be appended to it.
                # Therefor divides the objects in equivalence classes in a grid pattern: 1, 9 (3*3), 25 (5*5), 49 (7*7), 81 (9*9).
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

            # Calculates the average scale factor
            scale_factor = sum(scale_factors) / len(scale_factors)

            # Scales all nodes with the same factor.
            for node in nodes:
                node.scale(scale = Vector(scale_factor,scale_factor,scale_factor))

            # Checks scale message flag in settings file.
            if Blender.Blender.loadJsonFile('scale_message'):
                if message and not self._curasplit:
                    message.addAction('Open in Blender', i18n_catalog.i18nc('@action:button', 'Open in Blender'),
                                '[no_icon]', '[no_description]', button_align=Message.ActionButtonAlignment.ALIGN_LEFT)
                    message.addAction('Ignore', i18n_catalog.i18nc('@action:button', 'Ignore'),
                                '[no_icon]', '[no_description]', button_style=Message.ActionButtonStyle.SECONDARY, button_align=Message.ActionButtonAlignment.ALIGN_RIGHT)
                    message.actionTriggered.connect(self._openBlenderTrigger)
                    message.show()


    ##  The trigger connected with open blender function
    #
    #   \param message  The opened message to hide with ignore button.
    #   \param action   The pressed button on the message.
    def _openBlenderTrigger(self, message, action):
        if action == 'Open in Blender':
            if Blender.blender_path is None:
                QDesktopServices.openUrl(QUrl('https://www.blender.org/download/'))
            elif self._file_path is None:
                subprocess.Popen(Blender.blender_path, shell = True)
            else:
                subprocess.Popen((Blender.blender_path, self._file_path), shell = True)
        elif action == 'Ignore':
            message.hide()
        else:
            None
    

    ##  Converts the original file to a supported file extension based on prechosen preference and reads it.
    #
    #   \param file_path  The original path of the file we try to open.
    #   \param nodes      A list of nodes on which we will append all nodes contained in the file.
    #   \return           A temporary path of the converted file.
    def _convertAndOpenFile(self, file_path, nodes):
        # Checks, if file path contains the _curasplit_ flag (which indicates an already opened and split file -> important for reload).
        if '_curasplit_' not in file_path:
            command = self.buildCommand('Count nodes', file_path)
            objects = subprocess.run(command, shell = True, universal_newlines = True, stdout = subprocess.PIPE)
            # Checks output of our spawned subprocess which calculated the number of objects contained in the file.
            for nextline in objects.stdout.splitlines():
                if nextline.isdigit():
                    objects = int(nextline)
                    break

            # If file has no objects, return None.
            if objects == 0:
                return
            # Routine for files with exactly one object.
            elif objects == 1:
                temp_path = self._buildTempPath(file_path)
                import_file = self._importFile(temp_path)
                command = self.buildCommand('Single node', file_path, import_file)
                subprocess.run(command, shell = True)

                node = self._openFile(temp_path)
                node.getMeshData()._file_name = file_path
                nodes.append(node)
            # Routine for files with multiple objects.
            else:
                processes = []
                temp_paths = []
                # Gets all objects one by one in separate files with help of index. Does this parallely.
                for index in range(objects):
                    temp_path = self._buildTempPath(file_path, index)
                    import_file = self._importFile(temp_path)

                    command = self.buildCommand('Multiple nodes', file_path, import_file, str(index))
                    process = subprocess.Popen(command, shell = True)
                    processes.append(process)
                    temp_paths.append(temp_path)

                # Reads all newly created files.
                for (index, process, temp_path) in zip(range(objects), processes, temp_paths):
                    # Waits for possibly unfinished conversions.
                    process.wait()
                    node = self._openFile(temp_path)
                    node.getMeshData()._file_name = '{}_curasplit_{}.blend'.format(file_path[:-6], index + 1)
                    nodes.append(node)
        # If file was derived from another .blend file, instead checks the original file by index.
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


    ##  
    #
    #   \param file_path  The path of the original file.
    #   \param index      If file contains multiple objects, it indicates the number of the current object.
    #   \return           The path of the converted file.
    def _buildTempPath(self, file_path, index = None):
        if index:
            temp_path = '{}/cura_temp_{}_{}.{}'.format(os.path.dirname(file_path), str(random.random())[2:], index, Blender.file_extension)
        else:
            temp_path = '{}/cura_temp_{}.{}'.format(os.path.dirname(file_path), str(random.random())[2:], Blender.file_extension)

        return temp_path


    ##  Builds the command used by subprocess. Program inside the command is based on which mode gets called.
    #
    #   \param program      Mode used by the BlenderAPI to determine which program to run (set of instructions).
    #   \param file_path    The path of the original file.  
    #   \param instruction  String with the instruction for converting the file.
    #   \param index        If file contains multiple objects, it indicates the number of the current object.
    #   \return             The complete command needed by subprocess.
    @classmethod
    def buildCommand(self, program, file_path, instruction = None, index = None):
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
                # Our BlenderAPI uses sys.argv and the order of all arguments given to it needs to be fixed.
                command = command[:-1] + (instruction,) + command[-1:]
        else:
            command = (
                Blender.blender_path,
                '--background',
                '--python',
                self._script_path,
                '--', instruction, index, file_path, program
            )

        return command


    ##  Converts the original file into a new file with pre-choosed file extension.
    #
    #   \param  file_path  The original file path of the opened file.
    #   \return            String with the instruction for converting the file.
    def _importFile(self, file_path):
        if Blender.file_extension == 'stl' or Blender.file_extension == 'ply':
            import_file = 'bpy.ops.export_mesh.{}(filepath = "{}", check_existing = False)'.format(Blender.file_extension, file_path)
        elif Blender.file_extension == 'obj' or Blender.file_extension == 'x3d':
            import_file = 'bpy.ops.export_scene.{}(filepath = "{}", check_existing = False)'.format(Blender.file_extension, file_path)
        else:
            import_file = None
            Logger.logException('e', '%s is not supported!', Blender.file_extension)
        return import_file


    ##  Reads the converted file and removes it after that.
    #
    #   \param temp_path  The converted file to read.
    #   \return           The node contained in the readed file.
    def _openFile(self, temp_path):
        reader = Application.getInstance().getMeshFileHandler().getReaderForFile(temp_path)
        try:
            node = reader.read(temp_path)
        finally:
            if os.path.isfile(temp_path):
                os.remove(temp_path)
            # Converting to .obj always creates a copy of it as .mtl (A library for used materials).
            if os.path.isfile(temp_path[:-3] + 'mtl'):
                os.remove(temp_path[:-3] + 'mtl')
        return node
