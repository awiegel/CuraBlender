# Imports from the python standard library.
import os
import random
import subprocess
from subprocess import PIPE

# Imports from Uranium.
from UM.Mesh.MeshReader import MeshReader
from UM.Logger import Logger
from UM.Message import Message
from UM.Application import Application
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Math.Vector import Vector
from UM.i18n import i18nCatalog

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
    ##  Adds (stl, obj, x3d, ply) as supported file extensions for conversion.
    def __init__(self) -> None:
        super().__init__()
        # The supported extensions for converting the file.
        self._supported_extensions = ['.blend']
        self._supported_foreign_extensions = ['stl', 'obj', 'x3d', 'ply']


    ##  Main entry point for reading the file.
    #
    #   \param file_path  The path of the file we try to open.
    #   \return           A list of all nodes contained in the file.
    def read(self, file_path):
        # Checks if path to this plugin is set.
        if not Blender.plugin_path:
            Blender.Blender.setPluginPath()
        # Checks if path to blender is set or if it's the correct path, otherwise tries to set it.
        if not Blender.verified_blender and (not Blender.blender_path or not Blender.Blender.verifyBlenderPath()):
            Blender.Blender.setBlenderPath()

        # The return value: A list all nodes gets appended to. If file only contains one object, the list will be of length one.
        nodes = []

        # Only continues if correct path to blender is set.
        if not Blender.verified_blender:
            # Failure message already gets called at other place.
            Logger.logException('e', 'Problems with path to blender!')
        # Checks if file extension for conversion is supported (stl, obj, x3d, ply).
        elif Blender.file_extension not in self._supported_foreign_extensions:
            Logger.logException('e', '%s file extension is not supported!', Blender.file_extension)
            message = Message(text=i18n_catalog.i18nc('@info', '{} file extension is not supported!\nAllowed: {}'.format(Blender.file_extension, self._supported_foreign_extensions)),
                              title=i18n_catalog.i18nc('@info:title', 'Unsupported file extension'))
            message.show()
        # Path to blender and file extension is correct. Continues.
        else:
            self._curasplit = False
            self._check = False
            self._file_path = file_path

            temp_path = self._convertAndOpenFile(file_path, nodes)

            # Checks if file does not contain any objects.
            if temp_path == 'no_object':
                Logger.logException('e', '%s does not contain any objects!', file_path)
                message = Message(text=i18n_catalog.i18nc('@info', '{}\ndoes not contain any objects.'.format(file_path)),
                                  title=i18n_catalog.i18nc('@info:title', 'No object found'))
                message.show()
            # Checks if user has permission for path of current file.
            elif temp_path == 'no_permission':
                Logger.logException('e', '%s - write permission needed!', file_path)
                message = Message(text=i18n_catalog.i18nc('@info', 'Blender plugin needs write permission.\nPlease move your file or give permission.\n\nPath: {}'.format(file_path)),
                                  title=i18n_catalog.i18nc('@info:title', 'Not enough permission for this path'))
                message.show()
            # Checks if the file is too complex for aimed file extension.
            elif temp_path == 'complex_filetype':
                self._complexFileType()
            # Continues if file is converted correctly.  
            else:
                self._changeWatchedFile(temp_path, file_path)

                if not self._curasplit:
                    for node in DepthFirstIterator(Application.getInstance().getController().getScene().getRoot()):
                        if isinstance(node, CuraSceneNode):
                            # Checks if read is actually a reload or if the file is already opened and suppress the scaling message.
                            if file_path in node.getMeshData().getFileName() or file_path[:-6] + '_curasplit_' in node.getMeshData().getFileName():
                                self._curasplit = True
                                break

                self._calculateAndSetScale(nodes)

        return nodes


    # After reading exported file change file reference to .blend clone.
    def _changeWatchedFile(self, old_path, new_path):
        Application.getInstance().getController().getScene().removeWatchedFile(old_path)
        Blender.fs_watcher.addPath(new_path)


    # Reads all nodes contained in the file.
    # Calculates the needed scale factor based on equivalence classes and finally scales all nodes equally.
    def _calculateAndSetScale(self, nodes):
        # Checks auto scale flag in settings file.
        if Blender.Blender.loadJsonFile('auto_scale_on_read'):
            scale_factors = []
            # Calculates the scale factor for all nodes.
            for node in nodes:
                bounding_box = node.getBoundingBox()
                width = bounding_box.width
                height = bounding_box.height
                depth = bounding_box.depth

                message = None
                scale_factor = 1

                # Checks the minimum size of the object.
                if((min(width, height, depth)) < 5):
                    if not min(width, height, depth) == 0:
                        scale_factor = scale_factor * (5 / (scale_factor * min(width, height, depth)))
                        message = Message(text=i18n_catalog.i18nc('@info', 'Your object was too small and got scaled up to minimum print size.'),
                                          title=i18n_catalog.i18nc('@info:title', 'Object was too small'))
                # Checks the maximum height of the object.
                if(scale_factor * height) > 290:
                    scale_factor = scale_factor * (290 / (scale_factor * height))
                    message = Message(text=i18n_catalog.i18nc('@info', 'Your object was too high and got scaled down to maximum print size.'),
                                      title=i18n_catalog.i18nc('@info:title', 'Object was too high'))

                # Checks the maximum width/depth based on number of objects, because cura doesn't allow to manipulate the position of the object.
                # The first object gets loaded exactly in the middle and every other object will be appended to it.
                # Therefor divides the objects in equivalence classes in a grid pattern: 1, 9 (3*3), 25 (5*5), 49 (7*7), 81 (9*9).
                if len(nodes) == 1:
                    if((scale_factor * width) > 170) or ((scale_factor * depth) > 170):
                        scale_factor = scale_factor * (170 / (scale_factor * max(width, depth)))
                        message = Message(text=i18n_catalog.i18nc('@info', 'Your object was too broad and got scaled down to maximum print size.'),
                                          title=i18n_catalog.i18nc('@info:title', 'Object was too broad'))
                elif len(nodes) <= 9:
                    if((scale_factor * width) > (170 / 3)) or ((scale_factor * depth) > (170 / 3)):
                        scale_factor = scale_factor * ((170 / 3) / (scale_factor * max(width, depth)))
                        message = Message(text=i18n_catalog.i18nc('@info', 'Your objects were too broad together and got scaled down to maximum print size.'),
                                          title=i18n_catalog.i18nc('@info:title', 'Objects were too broad'))
                elif len(nodes) <= 25:
                    if((scale_factor * width) > (170 / 5)) or ((scale_factor * depth) > (170 / 5)):
                        scale_factor = scale_factor * ((170 / 5) / (scale_factor * max(width, depth)))
                        message = Message(text=i18n_catalog.i18nc('@info', 'Your objects were too broad together and got scaled down to maximum print size.'), 
                                          title=i18n_catalog.i18nc('@info:title', 'Objects were too broad'))
                elif len(nodes) <= 49:
                    if((scale_factor * width) > (170 / 7)) or ((scale_factor * depth) > (170 / 7)):
                        scale_factor = scale_factor * ((170 / 7) / (scale_factor * max(width, depth)))
                        message = Message(text=i18n_catalog.i18nc('@info', 'Your objects were too broad together and got scaled down to maximum print size.'),
                                          title=i18n_catalog.i18nc('@info:title', 'Objects were too broad'))
                elif len(nodes) <= 81:
                    if((scale_factor * width) > (170 / 9)) or ((scale_factor * depth) > (170 / 9)):
                        scale_factor = scale_factor * ((170 / 9) / (scale_factor * max(width, depth)))
                        message = Message(text=i18n_catalog.i18nc('@info', 'Your objects were too broad together and got scaled down to maximum print size.'),
                                          title=i18n_catalog.i18nc('@info:title', 'Objects were too broad'))
                else:
                    None

                scale_factors.append(scale_factor)

            # Calculates the average scale factor.
            scale_factor = sum(scale_factors) / len(scale_factors)

            # Scales all nodes with the same factor.
            for node in nodes:
                node.scale(scale = Vector(scale_factor,scale_factor,scale_factor))

            # Checks scale message flag in settings file.
            if Blender.Blender.loadJsonFile('show_scale_message'):
                if message and not self._curasplit:
                    message.addAction('Open in Blender', i18n_catalog.i18nc('@action:button', 'Open in Blender'), '[no_icon]', '[no_description]',
                                      button_align=Message.ActionButtonAlignment.ALIGN_LEFT)
                    message.addAction('Ignore', i18n_catalog.i18nc('@action:button', 'Ignore'), '[no_icon]', '[no_description]',
                                      button_style=Message.ActionButtonStyle.SECONDARY, button_align=Message.ActionButtonAlignment.ALIGN_RIGHT)
                    message.actionTriggered.connect(self._openBlenderTrigger)
                    message.show()


    ##  The trigger connected with open blender function.
    #
    #   \param message  The opened message to hide with ignore button.
    #   \param action   The pressed button on the message.
    def _openBlenderTrigger(self, message, action):
        if action == 'Open in Blender':
            command = '"{}" "{}"'.format(Blender.blender_path, self._file_path)
            subprocess.Popen(command, shell = True)
        message.hide()


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
                temp_path = 'no_object'
                return temp_path
            # Routine for files with exactly one object.
            elif objects == 1:
                temp_path = self._buildTempPath(file_path)
                import_file = self._importFile(temp_path)
                command = self.buildCommand('Single node', file_path, import_file)
                subprocess.run(command, shell = True)
                node = self._openFile(temp_path)
                # Checks if user has permission for path of current file.
                if self._check:
                    temp_path = self._check
                    return temp_path
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
                    # Checks if user has permission for path of current file.
                    if self._check:
                        temp_path = self._check
                    else:
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


    ##  Creates a temporary file with the random function to guarantee uniqueness. If multiple objects inside one file adds index.
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
        self._script_path = os.path.join(Blender.plugin_path, 'BlenderAPI.py')

        if program == 'Count nodes' or program == 'Single node':
            if instruction:
                # Our BlenderAPI uses sys.argv and the order of all arguments given to it needs to be fixed.
                command = '"{}" "{}" --background --python "{}" -- "{}" "{}"'.format(Blender.blender_path, file_path, self._script_path, instruction, program)
            else:
                command = '"{}" "{}" --background --python "{}" -- "{}"'.format(Blender.blender_path, file_path, self._script_path, program)
        else:
            command = '"{}" --background --python "{}" -- "{}" "{}" "{}" "{}"'.format(Blender.blender_path, self._script_path, instruction, index, file_path, program)

        return command


    ##  Converts the original file into a new file with prechosen file extension.
    #
    #   \param  file_path  The original file path of the opened file.
    #   \return            String with the instruction for converting the file.
    def _importFile(self, file_path):
        if Blender.file_extension == 'stl' or Blender.file_extension == 'ply':
            import_file = "bpy.ops.export_mesh.{}(filepath = '{}', check_existing = False)".format(Blender.file_extension, file_path)
        elif Blender.file_extension == 'obj' or Blender.file_extension == 'x3d':
            import_file = "bpy.ops.export_scene.{}(filepath = '{}', check_existing = False)".format(Blender.file_extension, file_path)
        else:
            # Unreachable statement, because allowed file extension got already verified.
            None
        return import_file


    ##  Reads the converted file and removes it after that.
    #
    #   \param temp_path  The converted file to read.
    #   \return           The node contained in the readed file.
    def _openFile(self, temp_path):
        reader = Application.getInstance().getMeshFileHandler().getReaderForFile(temp_path)
        try:
            if os.path.isfile(temp_path):
                node = reader.read(temp_path)
            else:
                self._check = 'no_permission'
        except:
            self._check = 'complex_filetype'
        finally:
            # In case procedure runs into errors and doesn't set node.
            if not 'node' in locals():
                node = None

            if os.path.isfile(temp_path):
                os.remove(temp_path)
            # Converting to .obj always creates a copy of it as .mtl (A library for used materials).
            if os.path.isfile(temp_path[:-3] + 'mtl'):
                os.remove(temp_path[:-3] + 'mtl')
        return node


    ## Creates message for too complex files.
    #
    #   \param file_path  The file_path of the complex object.
    def _complexFileType(self):
        Logger.logException('e', '%s is too complex for %s', Blender.file_extension, self._file_path)
        message = Message(text=i18n_catalog.i18nc('@info', 'This file is either too complex for {}-extension\nor no reader for this file type was found. \
                          \n\nPlease change the file extension:'.format(Blender.file_extension)),
                          title=i18n_catalog.i18nc('@info:title', '{} is not supported for this file'.format(Blender.file_extension)))
        if Blender.file_extension == 'stl':
            message.addAction('stl', i18n_catalog.i18nc('@action:button', 'stl'), '[no_icon]', '[no_description]',
                              button_style=Message.ActionButtonStyle.SECONDARY, button_align=Message.ActionButtonAlignment.ALIGN_LEFT)
            message.addAction('obj', i18n_catalog.i18nc('@action:button', 'obj'), '[no_icon]', '[no_description]',
                              button_align=Message.ActionButtonAlignment.ALIGN_LEFT)
            message.addAction('x3d', i18n_catalog.i18nc('@action:button', 'x3d'), '[no_icon]', '[no_description]',
                              button_align=Message.ActionButtonAlignment.ALIGN_LEFT)
            message.addAction('ply', i18n_catalog.i18nc('@action:button', 'ply'), '[no_icon]', '[no_description]',
                              button_align=Message.ActionButtonAlignment.ALIGN_LEFT)
        if Blender.file_extension == 'obj':
            message.addAction('stl', i18n_catalog.i18nc('@action:button', 'stl'), '[no_icon]', '[no_description]',
                              button_align=Message.ActionButtonAlignment.ALIGN_LEFT)
            message.addAction('obj', i18n_catalog.i18nc('@action:button', 'obj'), '[no_icon]', '[no_description]',
                              button_style=Message.ActionButtonStyle.SECONDARY, button_align=Message.ActionButtonAlignment.ALIGN_LEFT)
            message.addAction('x3d', i18n_catalog.i18nc('@action:button', 'x3d'), '[no_icon]', '[no_description]',
                              button_align=Message.ActionButtonAlignment.ALIGN_LEFT)
            message.addAction('ply', i18n_catalog.i18nc('@action:button', 'ply'), '[no_icon]', '[no_description]',
                              button_align=Message.ActionButtonAlignment.ALIGN_LEFT)
        if Blender.file_extension == 'x3d':
            message.addAction('stl', i18n_catalog.i18nc('@action:button', 'stl'), '[no_icon]', '[no_description]',
                              button_align=Message.ActionButtonAlignment.ALIGN_LEFT)
            message.addAction('obj', i18n_catalog.i18nc('@action:button', 'obj'), '[no_icon]', '[no_description]',
                              button_align=Message.ActionButtonAlignment.ALIGN_LEFT)
            message.addAction('x3d', i18n_catalog.i18nc('@action:button', 'x3d'), '[no_icon]', '[no_description]',
                              button_style=Message.ActionButtonStyle.SECONDARY, button_align=Message.ActionButtonAlignment.ALIGN_LEFT)
            message.addAction('ply', i18n_catalog.i18nc('@action:button', 'ply'), '[no_icon]', '[no_description]',
                              button_align=Message.ActionButtonAlignment.ALIGN_LEFT)
        if Blender.file_extension == 'ply':
            message.addAction('stl', i18n_catalog.i18nc('@action:button', 'stl'), '[no_icon]', '[no_description]',
                              button_align=Message.ActionButtonAlignment.ALIGN_LEFT)
            message.addAction('obj', i18n_catalog.i18nc('@action:button', 'obj'), '[no_icon]', '[no_description]',
                              button_align=Message.ActionButtonAlignment.ALIGN_LEFT)
            message.addAction('x3d', i18n_catalog.i18nc('@action:button', 'x3d'), '[no_icon]', '[no_description]',
                              button_align=Message.ActionButtonAlignment.ALIGN_LEFT)
            message.addAction('ply', i18n_catalog.i18nc('@action:button', 'ply'), '[no_icon]', '[no_description]',
                              button_style=Message.ActionButtonStyle.SECONDARY, button_align=Message.ActionButtonAlignment.ALIGN_LEFT)
        else:
            None
        message.actionTriggered.connect(self._changeFileType)
        message.show()


    ##  The trigger connected for changing file type if it's too complex.
    #
    #   \param message  The opened message to hide with ignore button.
    #   \param action   The pressed button on the message.
    def _changeFileType(self, message, action):
        if action == Blender.file_extension:
            fail_message = Message(text=i18n_catalog.i18nc('@info', 'Please choose a different file extension.'),
                                   title=i18n_catalog.i18nc('@info:title', 'Same file extension chosen'))
            fail_message.show()
        else:
            Blender.file_extension = action
            Blender.Blender.writeJsonFile('file_extension', action)
            message.hide()
            success_message = Message(text=i18n_catalog.i18nc('@info', 'File extension correctly changed.\n\nRetry loading the file.'),
                                      title=i18n_catalog.i18nc('@info:title', 'Change succesfully'))
            success_message.show()
