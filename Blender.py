# Imports from the python standard library.
import os
import json
import glob
import time  # Small fix for changes to live_reload during runtime.
import subprocess
from subprocess import PIPE

# Imports from QT.
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import QFileSystemWatcher, QUrl
from PyQt5.QtGui import QDesktopServices


# Imports from Uranium.
from UM.Platform import Platform
from UM.Logger import Logger
from UM.Message import Message
from UM.Tool import Tool  # The PluginObject we're going to extend.
from UM.PluginRegistry import PluginRegistry
from UM.Preferences import Preferences
from UM.Mesh.ReadMeshJob import ReadMeshJob  # To reload a mesh when its file was changed.
from UM.Application import Application
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Scene.Selection import Selection
from UM.i18n import i18nCatalog

# Imports from Cura.
from cura.Scene.CuraSceneNode import CuraSceneNode


# The catalog used for showing messages.
i18n_catalog = i18nCatalog('uranium')


# Global variables used by our other modules.
global plugin_path, fs_watcher, verified_plugin_path, verified_blender_path, outdated_blender_version

# A flag that indicates an already checked and confirmed plugin path.
verified_plugin_path = False
# A flag that indicates an already checked and confirmed blender version. 
verified_blender_path = False
# A flag that indicates an outdated blender version. 
outdated_blender_version = False


class Blender(Tool):
    """A Tool subclass and the main class for CuraBlender plugin."""

    def __init__(self):
        """The constructor, which calls the super-class-contructor (Tool).

        Loads and sets all settings from settings file.
        Adds .blend as a supported file extension.
        Adds (stl, obj, x3d, ply) as supported file extensions for conversion.
        Adds menu items and the filewatcher trigger function.
        """

        global fs_watcher
        super().__init__()

        # Loads and sets all settings from settings file.
        self.loadAndSetSettings()

        self._supported_extensions = ['.blend']
        self._supported_foreign_extensions = ['stl', 'obj', 'x3d', 'ply']

        # Adds filewatcher and it's connection for blender files.
        fs_watcher = QFileSystemWatcher()
        fs_watcher.fileChanged.connect(self._fileChanged)

        # Adds filewatcher and it's connection for foreign files.
        self._foreign_file_watcher = QFileSystemWatcher()
        self._foreign_file_watcher.fileChanged.connect(self._foreignFileChanged)


    def loadAndSetSettings(self):
        """Loads and sets all settings from settings file."""

        self._preferences = Application.getInstance().getPreferences()

        if not self._preferences._findPreference('cura_blender/live_reload'):
            self._preferences.addPreference('cura_blender/live_reload', True)
        if not self._preferences._findPreference('cura_blender/auto_arrange_on_reload'):
            self._preferences.addPreference('cura_blender/auto_arrange_on_reload', True)
        if not self._preferences._findPreference('cura_blender/auto_scale_on_read'):
            self._preferences.addPreference('cura_blender/auto_scale_on_read', True)
        if not self._preferences._findPreference('cura_blender/show_scale_message'):
            self._preferences.addPreference('cura_blender/show_scale_message', True)
        if not self._preferences._findPreference('cura_blender/file_extension'):
            self._preferences.addPreference('cura_blender/file_extension', 'stl')
        # Loads and sets the path to this plugin.
        self.loadPluginPath()

        # # Loads and sets the "live reload" option.
        # if self.loadJsonFile('live_reload'):
        #     self._live_reload = True
        # else:
        #     self._live_reload = False
        # # Loads and sets the "auto arrange on reload" option.
        # if self.loadJsonFile('auto_arrange_on_reload'):
        #     self._auto_arrange_on_reload = True
        # else:
        #     self._auto_arrange_on_reload = False
        # # Loads and sets the "auto scale on read" option.
        # if self.loadJsonFile('auto_scale_on_read'):
        #     self._auto_scale_on_read = True
        # else:
        #     self._auto_scale_on_read = False
        # # Loads and sets the "show scale message" option.
        # if self.loadJsonFile('show_scale_message'):
        #     self._show_scale_message = True
        # else:
        #     self._show_scale_message = False
        
        # Loads and sets the file extension.
        # self.loadFileExtension()

        # Loads and sets the path to blender.
        self.loadBlenderPath()


    # def loadFileExtension(self):
    #     """Loads and sets the file extension."""

    #     global file_extension
    #     file_extension = self.loadJsonFile('file_extension')
    #     if file_extension not in ['stl', 'obj', 'x3d', 'ply']:
    #         file_extension = 'stl'

    def loadPluginPath(self):
        """Loads and sets the path to this plugin."""

        global plugin_path
        for path_depth in range(10):
            depth = '/*' * path_depth
            plugin_path = glob.glob('{}{}/CuraBlender'.format(os.getcwd(), depth))
            if plugin_path:
                plugin_path = plugin_path[0].replace('\\', '/')
                break

    def loadBlenderPath(self):
        """Loads and sets the path to blender."""

        if not self._preferences._findPreference('cura_blender/blender_path'):
            self._preferences.addPreference('cura_blender/blender_path', '')


    def getLiveReload(self):
        """Gets the state of the "live reload" option."""

        return self._preferences.getValue('cura_blender/live_reload')
    
    def getAutoArrangeOnReload(self):
        """Gets the state of the "auto arrange on reload" option."""

        return self._preferences.getValue('cura_blender/auto_arrange_on_reload')
    
    def getAutoScaleOnRead(self):
        """Gets the state of the "auto scale on read" option."""

        return self._preferences.getValue('cura_blender/auto_scale_on_read')
    
    def getShowScaleMessage(self):
        """Gets the state of the "show scale message" option."""

        return self._preferences.getValue('cura_blender/show_scale_message')
    
    def getImportType(self):
        """Gets the current import type."""

        return self._preferences.getValue('cura_blender/file_extension')


    def setLiveReload(self, value):
        """Sets the state of the "live reload" option.

        :param value: The boolean value of the "live reload" option.
        """

        if value != self._preferences.getValue('cura_blender/live_reload'):
            self._preferences.setValue('cura_blender/live_reload', value)
            self.propertyChanged.emit()
    
    def setAutoArrangeOnReload(self, value):
        """Sets the state of the "auto arrange on reload" option.

        :param value: The boolean value of the "auto arrange on reload" option.
        """

        if value != self._preferences.getValue('cura_blender/auto_arrange_on_reload'):
            self._preferences.setValue('cura_blender/auto_arrange_on_reload', value)
            self.propertyChanged.emit()
    
    def setAutoScaleOnRead(self, value):
        """Sets the state of the "auto scale on read" option.

        :param value: The boolean value of the "auto scale on read" option.
        """

        if value != self._preferences.getValue('cura_blender/auto_scale_on_read'):
            self._preferences.setValue('cura_blender/auto_scale_on_read', value)
            self.propertyChanged.emit()
    
    def setShowScaleMessage(self, value):
        """Sets the state of the "show scale message" option.

        :param value: The boolean value of the "show scale message" option.
        """

        if value != self._preferences.getValue('cura_blender/show_scale_message'):
            self._preferences.setValue('cura_blender/show_scale_message', value)
            self.propertyChanged.emit()
    
    def setImportType(self, value):
        """Sets the import type to the given value.

        :param value: The given file_extension.
        """

        if value != self._preferences.getValue('cura_blender/file_extension'):
            self._preferences.setValue('cura_blender/file_extension', value)
            self.propertyChanged.emit()


    @classmethod
    def verifyPaths(self):
        """Checks if path to this plugin and path to blender are correct."""

        # Checks if path to this plugin is correct, otherwise sets it.
        if not verified_plugin_path and not self.verifyPluginPath():
            self.setPluginPath()
        # Checks if path to blender is set or if it's the correct path, otherwise tries to set it.
        if not verified_blender_path and (not Application.getInstance().getPreferences().getValue('cura_blender/blender_path') or not self.verifyBlenderPath()):
            self.setBlenderPath()

    @classmethod
    def setPluginPath(self):
        """Sets the path to this plugin."""

        global plugin_path, verified_plugin_path
        plugin_path = PluginRegistry.getInstance().getPluginPath('CuraBlender')
        verified_plugin_path = True

    @classmethod
    def verifyPluginPath(self):
        """Verifies the path to this plugin.
        
        :return: The boolean value of the correct plugin path.
        """

        global verified_plugin_path
        if os.path.exists(os.path.join(plugin_path, 'Blender.py')):
            verified_plugin_path = True
        return verified_plugin_path

    @classmethod
    def setBlenderPath(self, outdated = False):
        """Tries to set the path to blender automatically, if unsuccessful the user can set it manually.

        :param outdated: Flag if the found blender version is outdated.
        """

        global blender_path
        
        # Stops here because blender path from settings file is correct.
        if (not self.verifyBlenderPath() and not outdated_blender_version) or outdated:
            # Supports multi-platform
            if Platform.isWindows():
                temp_blender_path = glob.glob('C:/Program Files/Blender Foundation/**/*.exe')
                blender_path = temp_blender_path[len(temp_blender_path)-1].replace('\\', '/')
            elif Platform.isOSX():
                blender_path = '/Applications/Blender.app/Contents/MacOS/blender'
            elif Platform.isLinux():
                blender_path = '/usr/bin/blender'
            else:
                blender_path = None

            # If unsuccessful the user can set it manually.
            if not os.path.exists(blender_path):
                blender_path = self._openFileDialog(blender_path)
            else:
                self.verifyBlenderPath()

        # Adds blender path in settings file.
        Application.getInstance().getPreferences().setValue('cura_blender/blender_path', blender_path)


    @classmethod
    def verifyBlenderPath(self):
        """Verifies the path to blender.
        
        :return: The boolean value of the correct blender path.
        """

        global outdated_blender_version, verified_blender_path
        try:
            blender_path = Application.getInstance().getPreferences().getValue('cura_blender/blender_path')
            # Checks if blender path variable is set and the path really exists.
            if os.path.exists(blender_path):
                command = '"{}" --background --python-expr "import bpy; print(bpy.app.version >= (2, 80, 0))"'.format(blender_path)
                # Calls blender in the background and jumps to the exception if it's not blender and therefor returns false.
                # Also checks if the version of blender is compatible.
                version = subprocess.run(command, shell = True, universal_newlines = True, stdout = subprocess.PIPE)
                for nextline in version.stdout.splitlines():
                    if nextline == 'True':
                        verified_blender_path = True
                    elif nextline == 'False':
                        if not outdated_blender_version:
                            outdated_blender_version = True
                            Logger.logException('e', 'Your version of blender is outdated. Blender version 2.80 or higher is required!')
                            message = Message(text=i18n_catalog.i18nc('@info', 'Please update your blender version.'),
                                              title=i18n_catalog.i18nc('@info:title', 'Outdated blender version'))
                            message.addAction('Download Blender', i18n_catalog.i18nc('@action:button', 'Download Blender'), '[no_icon]', '[no_description]',
                                              button_align=Message.ActionButtonAlignment.ALIGN_LEFT)
                            message.addAction('Set new Blender path', i18n_catalog.i18nc('@action:button', 'Set new Blender path'), '[no_icon]', '[no_description]',
                                              button_style=Message.ActionButtonStyle.SECONDARY, button_align=Message.ActionButtonAlignment.ALIGN_RIGHT)
                            message.actionTriggered.connect(self._downloadBlenderTrigger)
                            message.show()
                    else:
                        None
        except:
            Logger.logException('e', 'Problems with path to blender!')
        finally:
            return verified_blender_path


    @classmethod
    def _downloadBlenderTrigger(self, message, action):
        """The trigger connected for downloading new blender version.

        :param message: The opened message to hide with ignore button.
        :param action: The pressed button on the message.
        """

        if action == 'Download Blender':
            QDesktopServices.openUrl(QUrl('https://www.blender.org/download/'))
        elif action == 'Set new Blender path':
            message.hide()
            self.setBlenderPath(outdated=True)
        else:
            None

    @classmethod
    def _openFileDialog(self, blender_path):
        """The user can set the path to blender manually. Gets called when blender isn't found in the expected place.

        :param blender_path: The global path to blender to set it. Here it's either wrong or doesn't exist.
        :return: The correctly set path to blender.
        """

        message = Message(text=i18n_catalog.i18nc('@info', 'Set your blender path manually.'),
                          title=i18n_catalog.i18nc('@info:title', 'Blender not found'))
        message.show()

        dialog = QFileDialog()
        dialog.setAcceptMode(QFileDialog.AcceptOpen)
        # Supports multi-platform
        if Platform.isWindows():
            dialog.setDirectory('C:/Program Files')
            dialog.setNameFilters(["Blender (*.exe)"])
        elif Platform.isOSX():
            dialog.setDirectory('/Applications')
            dialog.setNameFilters(["Blender (*.app)"])
        elif Platform.isLinux():
            dialog.setDirectory('/usr/bin')
        else:
            dialog.setDirectory('')

        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setViewMode(QFileDialog.Detail)
        # Opens the file explorer and checks if file is selected.
        if dialog.exec_():
            message.hide()
            self.verifyBlenderPath()
            # Adds blender path in settings file (needs permission).
            self._preferences.setValue('cura_blender/blender_path', blender_path)
        else:
            message.hide()
            message = Message(text=i18n_catalog.i18nc('@info', 'No blender path was selected.'),
                              title=i18n_catalog.i18nc('@info:title', 'Blender not found'))
            message.show()

        # Gets the selected blender path from file explorer.
        blender_path = ''.join(dialog.selectedFiles())
        return blender_path


    def openInBlender(self):
        """Checks if the selection of objects is correct and allowed and calls the actual function to open the file. """

        # Checks if path to this plugin and path to blender are correct.
        Blender.verifyPaths()

        # Only continues if correct path to blender is set.
        if verified_blender_path:
            # If no object is selected, check if the objects belong to more than one file.
            if len(Selection.getAllSelectedObjects()) == 0:
                open_files = set()
                for node in DepthFirstIterator(Application.getInstance().getController().getScene().getRoot()):
                    if isinstance(node, CuraSceneNode) and node.getMeshData().getFileName():
                        if '_curasplit_' in node.getMeshData().getFileName():
                            file_path = node.getMeshData().getFileName()
                            file_path = '{}.blend'.format(file_path[:file_path.index('_curasplit_')])
                        else:
                            file_path = node.getMeshData().getFileName()
                        open_files.add(file_path)
                # Opens the objects in blender, if they belong to only one file.
                if len(open_files) == 1:
                    self.openBlender(open_files.pop())
                else:
                    message = Message(text=i18n_catalog.i18nc('@info','Select Object first.'),
                                      title=i18n_catalog.i18nc('@info:title', 'Please select the object you want to open.'))
                    message.show()
            # If one object is selected, opens it's file reference (file name).
            elif len(Selection.getAllSelectedObjects()) == 1:
                for selection in Selection.getAllSelectedObjects():
                    file_path = selection.getMeshData().getFileName()
                    if '_curasplit_' in file_path:
                        file_path = '{}.blend'.format(file_path[:file_path.index('_curasplit_')])
                    self.openBlender(file_path)
            # If multiple objects are selected, checks if they belong to more than one file.
            else:
                files = set()
                for selection in Selection.getAllSelectedObjects():
                    file_path = selection.getMeshData().getFileName()
                    if '_curasplit_' in file_path:
                        file_path = '{}.blend'.format(file_path[:file_path.index('_curasplit_')])
                    files.add(file_path)
                # Opens the objects in blender, if they belong to only one file.
                if len(files) == 1:
                    self.openBlender(file_path)
                else:
                    message = Message(text=i18n_catalog.i18nc('@info','Please rethink your selection.'),
                                      title=i18n_catalog.i18nc('@info:title', 'Select only objects from same file'))
                    message.show()

    def openBlender(self, file_path):
        """Opens the given file in blender. File must not necessarily be a blender file.
     
        :param file_path: The path of the file to open in blender.
        """

        self._blender_path = Application.getInstance().getPreferences().getValue('cura_blender/blender_path')

        # Gets the extension of the file.
        current_file_extension = os.path.splitext(file_path)
        current_file_extension = current_file_extension[1][1:]

        # Checks if file is a blender file.
        if current_file_extension == 'blend':
            if '_curasplit_' in file_path:
                file_path = '{}.blend'.format(file_path[:file_path.index('_curasplit_')])
            command = '"{}" "{}"'.format(self._blender_path, file_path)
            subprocess.Popen(command, shell = True)
        # Procedure for non-blender files.
        elif current_file_extension in self._supported_foreign_extensions:
            execute_list = "bpy.data.objects.remove(bpy.data.objects['Cube']);"
            if current_file_extension == 'stl' or current_file_extension == 'ply':
                execute_list = execute_list + "bpy.ops.import_mesh.{}(filepath = '{}');".format(current_file_extension, file_path)
            elif current_file_extension == 'obj' or current_file_extension == 'x3d':
                execute_list = execute_list + "bpy.ops.import_scene.{}(filepath = '{}');".format(current_file_extension, file_path)
            else:
                None

            export_file = '{}/{}_cura_temp.blend'.format(os.path.dirname(file_path), os.path.basename(file_path).rsplit('.', 1)[0]).replace('//', '/')
            execute_list = execute_list + "bpy.ops.wm.save_as_mainfile(filepath = '{}')".format(export_file)

            command = '"{}" --background --python-expr "import bpy; import sys; exec(sys.argv[-1])" -- "{}"'.format(self._blender_path, execute_list)
            subprocess.run(command, shell = True)

            command = '"{}" "{}"'.format(self._blender_path, export_file)
            subprocess.Popen(command, shell = True)
            
            self._foreign_file_extension = os.path.basename(file_path).rsplit('.', 1)[-1]
            self._foreign_file_watcher.addPath(export_file)
        else:
            None


    def _foreignFileChanged(self, path):
        """On file changed connection. Rereads the changed file and updates it.
        
        This happens automatically and can be set on/off in the settings.
        Explicit for foreign file types (stl, obj, x3d, ply).

        :param path: The path to the changed foreign file.
        """

        export_path = '{}.{}'.format(path[:-6], self._foreign_file_extension)
        execute_list = "bpy.ops.export_mesh.{}(filepath = '{}', check_existing = False)".format(self._foreign_file_extension, export_path)

        command = '"{}" "{}" --background --python-expr "import bpy; import sys; exec(sys.argv[-1])" -- "{}"'.format(self._blender_path, path, execute_list)
        subprocess.run(command, shell = True)

        if self._preferences.getValue('cura_blender/live_reload') and os.path.isfile(export_path):
            job = ReadMeshJob(export_path)
            job.finished.connect(self._readMeshFinished)
            job.start()
            # Give process time while waiting for the job to finish.
            while not job.isFinished():
                job.yieldThread()
            # Remove temporary export file. Original foreign file, was not overwritten and the node still got it's reference in case of an undo.
            os.remove(export_path)

        if os.path.isfile(path + '1'):
            # Instead of overwriting files, blender saves the old one with .blend1 extension. We don't want this file at all, but need the original one for the file watcher.
            os.remove(path + '1')

        # Adds new filewatcher reference, because cura removes filewatcher automatically for other file types after reading.
        self._foreign_file_watcher.addPath(path)

    def _fileChanged(self, path):
        """On file changed connection. Rereads the changed file and updates it.
        
        This happens automatically and can be set on/off in the settings.

        :param path: The path to the changed blender file.
        """

        # Checks auto reload flag in settings file.
        if self._preferences.getValue('cura_blender/live_reload'):
            job = ReadMeshJob(path)
            job.finished.connect(self._readMeshFinished)
            job.start()
        # Refreshes file in file watcher in case the auto reload flag gets changed during runtime.
        else:
            time.sleep(1)
            fs_watcher.removePath(path)
            fs_watcher.addPath(path)

        if os.path.isfile(path + '1'):
            # Instead of overwriting files, blender saves the old one with .blend1 extension. We don't want this file at all, but need the original one for the file watcher.
            os.remove(path + '1')

    def _readMeshFinished(self, job):
        """On file changed connection. Rereads the changed file and updates it.
        
        This happens automatically and can be set on/off in the settings.

        :param path: The path to the changed file.
        """

        job._nodes = []
        temp_flag = False
        # Gets all files from all objects on the build plate.
        for node in DepthFirstIterator(Application.getInstance().getController().getScene().getRoot()):
            if isinstance(node, CuraSceneNode) and node.getMeshData():
                file_path = node.getMeshData().getFileName()
                # Gets the original file name of _curasplit_ objects.
                if '_curasplit_' in file_path:
                    file_path = '{}.blend'.format(file_path[:file_path.index('_curasplit_')])

                # Checks if foreign file gets reloaded.
                if '_cura_temp' in job.getFileName():
                    temp_path = '{}/{}.{}'.format(os.path.dirname(job.getFileName()),                          \
                                                  os.path.basename(job.getFileName()).rsplit('.', 1)[0][:-10], \
                                                  os.path.basename(job.getFileName()).rsplit('.', 1)[-1]).replace('//', '/')
                    if file_path == temp_path:
                        job._nodes.append(node)
                        temp_flag = True
                else:
                    if file_path == job.getFileName():
                        job._nodes.append(node)

        # Important for reloading blender files with multiple objects. Gets the correctly changed object by it's index.
        job_result = job.getResult()
        index = 0
        dif = len(job_result) - len(job._nodes)
        for d in range(dif):
            job._nodes.insert(d, '')

        for (node, job._node) in zip(job_result, job._nodes):
            if index < dif:
                index += 1
                continue
            mesh_data = node.getMeshData()
            job._node.setMeshData(mesh_data)
            # Checks if foreign file is reloaded and sets the correct file name.
            if temp_flag:
                job._node.getMeshData()._file_name = temp_path

        # Checks auto arrange flag in settings file.
        if self._preferences.getValue('cura_blender/auto_arrange_on_reload'):
            # Arranges the complete build plate after reloading a file. Can be set on/off in the settings.
            Application.getInstance().arrangeAll()
