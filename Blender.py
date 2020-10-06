# Imports from the python standard library.
import os
import glob
import time  # Small fix for changes to live_reload during runtime.
import subprocess
from subprocess import PIPE

# Imports from QT.
from PyQt5.QtWidgets import QFileDialog, QInputDialog
from PyQt5.QtCore import QFileSystemWatcher, QUrl
from PyQt5.QtGui import QDesktopServices

# Imports from Uranium.
from UM.Platform import Platform
from UM.Logger import Logger
from UM.Message import Message
from UM.Extension import Extension  # The PluginObject we're going to extend.
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
catalog = i18nCatalog('cura')


# Global variables used by our other modules.
global fs_watcher, verified_blender_path, outdated_blender_version

# A flag that indicates an already checked and confirmed blender version. 
verified_blender_path = False
# A flag that indicates an outdated blender version. 
outdated_blender_version = False


class Blender(Extension):
    """An Extension subclass and the main class for CuraBlender plugin."""

    def __init__(self):
        """The constructor, which calls the super-class-contructor (Extension).

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

        # Builds the extension menu.
        self.setMenuName(catalog.i18nc('@item:inmenu', 'CuraBlender'))
        self.addMenuItem(catalog.i18nc('@item:inmenu', 'Open in Blender'), self._setUpFilePathForBlender)
        self.addMenuItem(catalog.i18nc('@item:inmenu', 'Settings'), self._openSettingsWindow)
        self.addMenuItem(catalog.i18nc('@item:inmenu', 'Debug Blenderpath'), self._showBlenderPath)


    def _openSettingsWindow(self):
        """Opens the settings."""

        qml_file_path = os.path.join(PluginRegistry.getInstance().getPluginPath(self.getPluginId()), 'BlenderTool.qml')
        self._console_window = Application.getInstance().createQmlComponent(qml_file_path, {'manager': self})
        self._console_window.show()


    def _showBlenderPath(self):
        """Shows the current blender path and gives the option to set a new path."""

        message = Message(text=catalog.i18nc('@info', Application.getInstance().getPreferences().getValue('cura_blender/blender_path')),
                          title=catalog.i18nc('@info:title', 'Currently set path to Blender'))
        message.addAction('FileDialog', catalog.i18nc('@action:button', 'Open File Explorer'), '[no_icon]', '[no_description]',
                          button_align=Message.ActionButtonAlignment.ALIGN_LEFT)
        message.addAction('InputDialog', catalog.i18nc('@action:button', 'Open Text Field'), '[no_icon]', '[no_description]',
                          button_style=Message.ActionButtonStyle.SECONDARY, button_align=Message.ActionButtonAlignment.ALIGN_RIGHT)
        message.actionTriggered.connect(self._setBlenderPathTrigger)
        message.show()


    def _setBlenderPathTrigger(self, message, action):
        """The trigger connected with show blender path function.

        :param message: The opened message to hide with ignore button.
        :param action: The pressed button on the message.
        """

        message.hide()
        if action == 'FileDialog':
            self._openFileDialog()
        elif action == 'InputDialog':
            self._openInputDialog()
        else:
            None


    def loadAndSetSettings(self):
        """Loads and sets all settings from preferences."""

        self._preferences = Application.getInstance().getPreferences()

        # Loads and sets the 'live reload' setting.
        if not self._preferences._findPreference('cura_blender/live_reload'):
            self._preferences.addPreference('cura_blender/live_reload', True)
        # Loads and sets the 'auto_arrange_on_reload' setting.
        if not self._preferences._findPreference('cura_blender/auto_arrange_on_reload'):
            self._preferences.addPreference('cura_blender/auto_arrange_on_reload', True)
        # Loads and sets the 'auto_scale_on_read' setting.
        if not self._preferences._findPreference('cura_blender/auto_scale_on_read'):
            self._preferences.addPreference('cura_blender/auto_scale_on_read', True)
        # Loads and sets the 'show_scale_message' setting.
        if not self._preferences._findPreference('cura_blender/show_scale_message'):
            self._preferences.addPreference('cura_blender/show_scale_message', True)
        # Loads and sets the file extension.
        if not self._preferences._findPreference('cura_blender/file_extension'):
            self._preferences.addPreference('cura_blender/file_extension', 'stl')
        # Loads and sets the 'warn_before_closing_other_blender_instances' setting. !!! Caution !!!
        if not self._preferences._findPreference('cura_blender/warn_before_closing_other_blender_instances'):
            self._preferences.addPreference('cura_blender/warn_before_closing_other_blender_instances', True)
        # Loads and sets the path to blender.
        if not self._preferences._findPreference('cura_blender/blender_path'):
            self._preferences.addPreference('cura_blender/blender_path', '')


    @classmethod
    def getPluginPath(self):
        """Gets the path to this plugin.

        :return: The path to this plugin.
        """

        plugin_path = PluginRegistry.getInstance().getPluginPath('CuraBlender')
        return plugin_path


    @classmethod
    def verifyBlenderPath(self, manual = False):
        """Verifies the path to blender.
        
        :param manual: If path was set manually, does not open file explorer on wrong path.
        :return: The boolean value of the correct blender path.
        """

        global outdated_blender_version, verified_blender_path
        try:
            # Checks if path to blender is already verified.
            if not verified_blender_path:
                blender_path = Application.getInstance().getPreferences().getValue('cura_blender/blender_path')
                # Checks if blender path is set and the path really exists.
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
                                message = Message(text=catalog.i18nc('@info', 'Please update your blender version.'),
                                                title=catalog.i18nc('@info:title', 'Outdated blender version'))
                                message.addAction('Download Blender', catalog.i18nc('@action:button', 'Download Blender'), '[no_icon]', '[no_description]',
                                                button_align=Message.ActionButtonAlignment.ALIGN_LEFT)
                                message.addAction('Set new Blender path', catalog.i18nc('@action:button', 'Set new Blender path'), '[no_icon]', '[no_description]',
                                                button_style=Message.ActionButtonStyle.SECONDARY, button_align=Message.ActionButtonAlignment.ALIGN_RIGHT)
                                message.actionTriggered.connect(self._downloadBlenderTrigger)
                                message.show()
                        else:
                            None
                # Checks if path to blender is finally verified.
                if manual and not verified_blender_path:
                    message = Message(text=catalog.i18nc('@info', 'Could not verify your path.'),
                                      title=catalog.i18nc('@info:title', 'Wrong path'))
                    message.show()
                elif not verified_blender_path:
                    self.setBlenderPath()
                else:
                    None
        except:
            Logger.logException('e', 'Problems with path to blender!')
        finally:
            return verified_blender_path

    @classmethod
    def setBlenderPath(self, outdated = False):
        """Tries to set the path to blender automatically, if unsuccessful the user can set it manually.

        :param outdated: Flag if the found blender version is outdated.
        """

        # Stops here because blender path from settings file is correct.
        if not outdated_blender_version or outdated:
            # Supports multi-platform
            if Platform.isWindows():
                temp_blender_path = glob.glob('C:/Program Files/Blender Foundation/**/*.exe')
                blender_path = temp_blender_path[len(temp_blender_path)-1].replace('\\', '/')
            elif Platform.isOSX():
                blender_path = '/Applications/Blender.app/Contents/MacOS/Blender'
            elif Platform.isLinux():
                blender_path = '/usr/bin/blender'
            else:
                blender_path = None

            # If unsuccessful the user can set it manually.
            if not os.path.exists(blender_path):
                self._openFileDialog()
            else:
                # Adds blender path in settings file.
                Application.getInstance().getPreferences().setValue('cura_blender/blender_path', blender_path)
                self.verifyBlenderPath(manual=False)

    @classmethod
    def _openFileDialog(self):
        """The user can set the path to blender manually. Gets called when blender isn't found in the expected place."""

        global verified_blender_path
        message = Message(text=catalog.i18nc('@info', 'Set your blender path manually.'),
                          title=catalog.i18nc('@info:title', 'Blender not found'))
        message.show()

        dialog = QFileDialog()
        dialog.setAcceptMode(QFileDialog.AcceptOpen)
        # Supports multi-platform
        if Platform.isWindows():
            dialog.setDirectory('C:/Program Files')
            dialog.setNameFilters(["Blender (*.exe)"])
        elif Platform.isOSX():
            dialog.setDirectory('/Applications')
        elif Platform.isLinux():
            dialog.setDirectory('/usr/bin')
        else:
            dialog.setDirectory('')

        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setViewMode(QFileDialog.Detail)
        # Opens the file explorer and checks if file is selected.
        if dialog.exec_():
            message.hide()
            # Gets the selected blender path from file explorer.
            Application.getInstance().getPreferences().setValue('cura_blender/blender_path', ''.join(dialog.selectedFiles()))
            verified_blender_path = False
            self.verifyBlenderPath(manual=True)
            message = Message(text=catalog.i18nc('@info', Application.getInstance().getPreferences().getValue('cura_blender/blender_path')),
                              title=catalog.i18nc('@info:title', 'New Blenderpath set'))
            message.show()
        else:
            message.hide()
            message = Message(text=catalog.i18nc('@info', 'No blender path was selected.'),
                              title=catalog.i18nc('@info:title', 'Blender not found'))
            message.show()

    def _openInputDialog(self):
        """The user can set the path to blender manually. Gets called when blender isn't found in the expected place."""

        global verified_blender_path
        text = QInputDialog.getText(QInputDialog(), 'Blender path', 'Enter your path to Blender:')
        if text[1] and text[0] != '':
            Application.getInstance().getPreferences().setValue('cura_blender/blender_path', text[0])
            verified_blender_path = False
            self.verifyBlenderPath(manual=True)

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


    # Grouped objects cannot be opened with blender due to mixed file reference.
    def _checkGrouped(self):
        """Checks if the selected objects are grouped.

        :return: The boolean value if objects are grouped.
        """

        is_grouped = False
        for selection in Selection.getAllSelectedObjects():
            if selection.callDecoration("isGroup"):
                is_grouped = True
                message = Message(text=catalog.i18nc('@info','Ungroup selected group?'),
                                  title=catalog.i18nc('@info:title', 'Only nodes without group are allowed.'))
                message.addAction('Ungroup', catalog.i18nc('@action:button', 'Ungroup'), '[no_icon]', '[no_description]',
                                  button_align=Message.ActionButtonAlignment.ALIGN_LEFT)
                message.addAction('Ignore', catalog.i18nc('@action:button', 'Ignore'), '[no_icon]', '[no_description]',
                                  button_style=Message.ActionButtonStyle.SECONDARY, button_align=Message.ActionButtonAlignment.ALIGN_RIGHT)
                message.actionTriggered.connect(self._ungroupTrigger)
                message.show()
        return is_grouped

    def _ungroupTrigger(self, message, action):
        """The trigger connected with check grouped function.

        :param message: The opened message to hide with ignore button.
        :param action: The pressed button on the message.
        """

        if action == 'Ungroup':
            Application.getInstance().ungroupSelected()
            message.hide()
            message = Message(text=catalog.i18nc('@info','Select a new object to open in blender!'),
                              title=catalog.i18nc('@info:title', 'Your objects were ungrouped.'))
            message.show()
        else:
            message.hide()


    def _setUpFilePathForBlender(self):
        """Checks if the selection of objects is correct and allowed and calls the function to build the command. """

        # Checks if path to this plugin and path to blender are correct.
        Blender.verifyBlenderPath(manual=False)

        # Only continues if correct path to blender is set.
        if verified_blender_path and not self._checkGrouped():
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
                    self._buildCommandForBlender(open_files.pop())
                else:
                    message = Message(text=catalog.i18nc('@info','Select Object first.'),
                                      title=catalog.i18nc('@info:title', 'Please select the object you want to open.'))
                    message.show()
            # If one object is selected, opens it's file reference (file name).
            elif len(Selection.getAllSelectedObjects()) == 1:
                for selection in Selection.getAllSelectedObjects():
                    file_path = selection.getMeshData().getFileName()
                    if '_curasplit_' in file_path:
                        file_path = '{}.blend'.format(file_path[:file_path.index('_curasplit_')])
                    self._buildCommandForBlender(file_path)
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
                    self._buildCommandForBlender(file_path)
                else:
                    message = Message(text=catalog.i18nc('@info','Please rethink your selection.'),
                                      title=catalog.i18nc('@info:title', 'Select only objects from same file'))
                    message.show()

    def _buildCommandForBlender(self, file_path):
        """Builds the command to open the given file in blender. File must not necessarily be a blender file.
     
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

            self._foreign_file_extension = os.path.basename(file_path).rsplit('.', 1)[-1]
            self._foreign_file_watcher.addPath(export_file)
        else:
            None

        self.openInBlender(command)


    @classmethod
    def openInBlender(self, command):
        """Executes the given command. Asks for closing all other instances of blender.

        !!! Caution !!!
        Terminates all instances of blender without saving. Potential loss of data.

        :param command: The command to open the file in blender.
        """

        self._command = command

        # Checks warn before closing other blender instances flag in settings file.
        if Application.getInstance().getPreferences().getValue('cura_blender/warn_before_closing_other_blender_instances'):
            message = Message(text=catalog.i18nc('@info','This will close all other instances of blender without saving.\nPotential loss of data.'),
                            title=catalog.i18nc('@info:title', 'Caution!'))
            message.addAction('Continue', catalog.i18nc('@action:button', 'Continue'), '[no_icon]', '[no_description]',
                            button_align=Message.ActionButtonAlignment.ALIGN_LEFT)
            message.addAction('Ignore', catalog.i18nc('@action:button', "Don't show this message again"), '[no_icon]', '[no_description]',
                            button_style=Message.ActionButtonStyle.SECONDARY, button_align=Message.ActionButtonAlignment.ALIGN_RIGHT)
            message.actionTriggered.connect(self._closeAllBlenderInstancesTrigger)
            message.show()
        else:
            # Executes the command to open the file in blender.
            subprocess.Popen(self._command, shell = True)

    @classmethod
    def _closeAllBlenderInstancesTrigger(self, message, action):
        """The trigger connected with check grouped function.

        :param message: The opened message to hide with ignore button.
        :param action: The pressed button on the message.
        """

        if action == 'Continue':
            blender_path = Application.getInstance().getPreferences().getValue('cura_blender/blender_path')

            if Platform.isWindows():
                command = '"taskkill" "/f" "/im" "{}"'.format(os.path.basename(blender_path))
            else:
                command = '"pkill" "-f" "{}"'.format(os.path.basename(blender_path))
            subprocess.call(command, shell = True)
            # Executes the command to open the file in blender.
            subprocess.Popen(self._command, shell = True)
        elif action == 'Ignore':
            Application.getInstance().getPreferences().setValue('cura_blender/warn_before_closing_other_blender_instances', False)
        else:
            None
        message.hide()


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
