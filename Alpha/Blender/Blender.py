# Imports from the python standard library.
import os
import platform
import glob
import subprocess
import json

# Imports from QT.
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import QFileSystemWatcher

# Imports from Uranium.
from UM.Logger import Logger
from UM.Message import Message
from UM.Tool import Tool  # The PluginObject we're going to extend.
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
global blender_path, file_extension, fs_watcher


##  Main class for blender plugin.
class Blender(Tool):
    ##  The constructor, which calls the super-class-contructor (Tool).
    ##  Loads and sets all settings from settings file.
    ##  Adds .blend as a supported file extension.
    ##  Adds (stl, obj, x3d, ply) as supported file extensions for conversion.
    ##  Adds menu items and the filewatcher trigger function.
    def __init__(self):
        global fs_watcher
        super().__init__()

        # Loads and sets all settings from settings file.
        self.loadAndSetSettings()

        self._supported_extensions = ['.blend']
        self._supported_foreign_extensions = ['stl', 'obj', 'x3d', 'ply']
        
        # Properties used by the qml file.
        self.setExposedProperties("LiveReload", "AutoArrangeOnReload", "AutoScaleOnRead", "ShowScaleMessage", "ImportType")

        # Adds filewatcher and it's connection for blender files.
        fs_watcher = QFileSystemWatcher()
        fs_watcher.fileChanged.connect(self.fileChanged)

        # Adds filewatcher and it's connection for foreign files.
        self._foreign_file_watcher = QFileSystemWatcher()
        self._foreign_file_watcher.fileChanged.connect(self._foreignFileChanged)


    ##  Loads value from settings file (blender_settings.json) based on key.
    #
    #   \param key  The key inside the settings file.
    #   \return     The value associated with the given key.
    @classmethod
    def loadJsonFile(self, key):
        with open('plugins/Blender/blender_settings.json', 'r') as json_file:
            data = json.load(json_file)
        return data[key]
    

    ##  Loads the settings file (blender_settings.json) and tries to store the value to the given key.
    ##  The settings file (blender_settings.json) needs to have write permission for current user.
    ##  If no permissions are granted, no changes won't be saved to the settings file and user needs to change settings manually.
    #
    #   \param key    The key inside the settings file.
    #   \param value  The value we try to add to the requested key.
    @classmethod
    def writeJsonFile(self, key, value):
        with open('plugins/Blender/blender_settings.json', 'r') as json_file:
            data = json.load(json_file)

        # Needs write permissions for the settings file (blender_settings.json).
        try:
            with open('plugins/Blender/blender_settings.json', 'w+') as outfile:
                data[key] = value
                json.dump(data, outfile, indent=4, sort_keys=False)
        except:
            None


    ## Loads and sets all settings from settings file.
    def loadAndSetSettings(self):
        # Loads and sets the "live reload" option.
        if self.loadJsonFile('live_reload'):
            self._live_reload = True
        else:
            self._live_reload = False
        # Loads and sets the "auto arrange on reload" option.
        if self.loadJsonFile('auto_arrange_on_reload'):
            self._auto_arrange_on_reload = True
        else:
            self._auto_arrange_on_reload = False
        # Loads and sets the "auto scale on read" option.
        if self.loadJsonFile('auto_scale_on_read'):
            self._auto_scale_on_read = True
        else:
            self._auto_scale_on_read = False
        # Loads and sets the "show scale message" option.
        if self.loadJsonFile('show_scale_message'):
            self._show_scale_message = True
        else:
            self._show_scale_message = False
        
        # Loads and sets the file extension.
        self.loadFileExtension()

        # Loads and sets the path to blender.
        self.loadBlenderPath()


    ## Loads and sets the file extension.
    def loadFileExtension(self):
        global file_extension
        file_extension = self.loadJsonFile('file_extension')

    ## Loads and sets the path to blender.
    def loadBlenderPath(self):
        global blender_path
        blender_path = self.loadJsonFile('blender_path')
    

    ## Gets the state of the "live reload" option.
    def getLiveReload(self):
        return self._live_reload
    
    ## Gets the state of the "auto arrange on reload" option.
    def getAutoArrangeOnReload(self):
        return self._auto_arrange_on_reload
    
    ## Gets the state of the "auto scale on read" option.
    def getAutoScaleOnRead(self):
        return self._auto_scale_on_read
    
    ## Gets the state of the "show scale message" option.
    def getShowScaleMessage(self):
        return self._show_scale_message
    
    ## Gets the current import type.
    def getImportType(self):
        return file_extension


    ## Sets the state of the "live reload" option.
    def setLiveReload(self, value):
        if value != self._live_reload:
            self._live_reload = value
            self.propertyChanged.emit()
            self.writeJsonFile('live_reload', value)
    
    ## Sets the state of the "auto arrange on reload" option.
    def setAutoArrangeOnReload(self, value):
        if value != self._auto_arrange_on_reload:
            self._auto_arrange_on_reload = value
            self.propertyChanged.emit()
            self.writeJsonFile('auto_arrange_on_reload', value)
    
    ## Sets the state of the "auto scale on read" option.
    def setAutoScaleOnRead(self, value):
        if value != self._auto_scale_on_read:
            self._auto_scale_on_read = value
            self.propertyChanged.emit()
            self.writeJsonFile('auto_scale_on_read', value)
    
    ## Sets the state of the "show scale message" option.
    def setShowScaleMessage(self, value):
        if value != self._show_scale_message:
            self._show_scale_message = value
            self.propertyChanged.emit()
            self.writeJsonFile('show_scale_message', value)
    
    ## Sets the import type to the given value.
    def setImportType(self, value):
        global file_extension
        if value != file_extension:
            file_extension = value
            self.propertyChanged.emit()
            self.writeJsonFile('file_extension', value)


    ##  Tries to set the path to blender automatically, if unsuccessful the user can set it manually.
    @classmethod
    def setBlenderPath(self):
        global blender_path
        # Checks blender path in settings file.
        if self.loadJsonFile('blender_path'):
            blender_path = self.loadJsonFile('blender_path')
        
        # Stops here because blender path from settings file is correct.
        if not self.verifyBlenderPath():
            system = platform.system()
            # Supports multi-platform
            if system == 'Windows':
                temp_blender_path = glob.glob('C:/Program Files/Blender Foundation/**/*.exe')
                blender_path = ''.join(temp_blender_path).replace('\\', '/')
            elif system == 'Darwin':
                blender_path = '/Applications/Blender.app/Contents/MacOS/blender'
            elif system == 'Linux':
                blender_path = '/usr/share/blender/2.82/blender'
            else:
                blender_path = None

            # If unsuccessful the user can set it manually.
            if not os.path.exists(blender_path):
                blender_path = self._openFileDialog(blender_path, system)
            # Adds blender path in settings file (needs permission).
            self.writeJsonFile('blender_path', blender_path)


    ##  Verifies the path to blender.
    @classmethod
    def verifyBlenderPath(self):
        correct_blender_path = False
        try:
            # Checks if blender path variable is set and the path really exists.
            if blender_path and os.path.exists(blender_path):
                # Calls blender in the background and jumps to the exception if it's not blender and therefor returns false.
                subprocess.check_call((blender_path, '--background'), shell=True)
                correct_blender_path = True
        except:
            Logger.logException('e', 'Problems with path to blender!')
        finally:
            return correct_blender_path


    ##  The user can set the path to blender manually. Gets called when blender isn't found in the expected place.
    #
    #   \param blender_path  The global path to blender to set it. Here it's either wrong or doesn't exist.
    #   \param system        The operating system from which the user operates.
    #   \return              The correctly set path to blender.
    @classmethod
    def _openFileDialog(self, blender_path, system):
        message = Message(text=i18n_catalog.i18nc('@info', 'Set your blender path manually'),
                          title=i18n_catalog.i18nc('@info:title', 'Blender not found'))
        message.show()
        dialog = QFileDialog()
        dialog.setAcceptMode(QFileDialog.AcceptOpen)
        # Supports multi-platform
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
        # Opens the file explorer and checks if file is selected.
        if dialog.exec_():
            message.hide()
        else:
            message.hide()
            message = Message(text=i18n_catalog.i18nc('@info', 'No blender path was selected'),
                              title=i18n_catalog.i18nc('@info:title', 'Blender not found'))
            message.show()
        # Gets the selected blender path from file explorer.
        blender_path = ''.join(dialog.selectedFiles())
        return blender_path


    ##  Checks if the selection of objects is correct and allowed and calls the actual function to open the file. 
    def openInBlender(self):
        # Checks if path to blender is set or if it's the correct path, otherwise tries to set it.
        if not blender_path or not self.verifyBlenderPath():
            self.setBlenderPath()

        # Only continues if correct path to blender is set.
        if self.verifyBlenderPath():
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
                    message = Message(text=i18n_catalog.i18nc('@info','Select Object first'),
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


    ##  Opens the given file in blender. File must not necessarily be a blender file.
    #
    #   \param file_path  The path of the file to open in blender.
    def openBlender(self, file_path):
        # Gets the extension of the file.
        current_file_extension = os.path.basename(file_path).partition('.')[2]
        # Checks if file is a blender file.
        if current_file_extension == 'blend':
            if '_curasplit_' in file_path:
                file_path = '{}.blend'.format(file_path[:file_path.index('_curasplit_')])
            subprocess.Popen((blender_path, file_path), shell = True)
        # Procedure for non-blender files.
        elif current_file_extension in self._supported_foreign_extensions:
            execute_list = 'bpy.data.objects.remove(bpy.data.objects["Cube"]);'
            if current_file_extension == 'stl' or current_file_extension == 'ply':
                execute_list = execute_list + 'bpy.ops.import_mesh.{}(filepath = "{}");'.format(current_file_extension, file_path)
            elif current_file_extension == 'obj' or current_file_extension == 'x3d':
                execute_list = execute_list + 'bpy.ops.import_scene.{}(filepath = "{}");'.format(current_file_extension, file_path)
            else:
                None

            export_file = '{}/{}_cura_temp.blend'.format(os.path.dirname(file_path), os.path.basename(file_path).rsplit('.', 1)[0])
            execute_list = execute_list + 'bpy.ops.wm.save_as_mainfile(filepath = "{}")'.format(export_file)

            command = (
                blender_path,
                '--background',
                '--python-expr',
                'import bpy;'
                'import sys;'
                'exec(sys.argv[-1])',
                '--', execute_list
            )
            subprocess.run(command, shell = True)

            subprocess.Popen((blender_path, export_file), shell = True)
            

            self._foreign_file_extension = os.path.basename(file_path).rsplit('.', 1)[-1]
            self._foreign_file_watcher.addPath(export_file)
        else:
            None

    
    ##  On file changed connection. Rereads the changed file and updates it. This happens automatically and can be set on/off in the settings.
    ##  Explicit for foreign file types (stl, obj, x3d, ply).
    #
    #   \param path  The path to the changed foreign file.
    def _foreignFileChanged(self, path):
        export_path = '{}.{}'.format(path[:-6], self._foreign_file_extension)
        execute_list = 'bpy.ops.export_mesh.{}(filepath = "{}", check_existing = False)'.format(self._foreign_file_extension, export_path)
        command = (
            blender_path,
            path,
            '--background',
            '--python-expr',
            'import bpy;'
            'import sys;'
            'exec(sys.argv[-1])',
            '--', execute_list
        )
        subprocess.run(command, shell = True)

        job = ReadMeshJob(export_path)
        job.finished.connect(self._readMeshFinished)
        job.start()
        # Instead of overwriting files, blender saves the old one with .blend1 extension. We don't want this file at all, but need the original one for the file watcher.
        os.remove(path + '1')
        # Adds new filewatcher reference, because cura removes filewatcher automatically for other file types after reading.
        self._foreign_file_watcher.addPath(path)
    

    ##  On file changed connection. Rereads the changed file and updates it. This happens automatically and can be set on/off in the settings.
    #
    #   \param path  The path to the changed blender file.
    def fileChanged(self, path):
        # Checks auto reload flag in settings file.
        if self.live_reload:
            job = ReadMeshJob(path)
            job.finished.connect(self._readMeshFinished)
            job.start()
        # Adds file to file watcher in case the auto reload flag gets changed during runtime.
        else:
            fs_watcher.addPath(path)


    ##  On file changed connection. Rereads the changed file and updates it. This happens automatically and can be set on/off in the settings.
    #
    #   \param path  The path to the changed file.
    def _readMeshFinished(self, job):
        job._nodes = []
        tempFlag = False
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
                                                  os.path.basename(job.getFileName()).rsplit('.', 1)[-1])
                    if file_path == temp_path:
                        job._nodes.append(node)
                        tempFlag = True
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
            if tempFlag:
                job._node.getMeshData()._file_name = temp_path

        # Checks auto arrange flag in settings file.
        if self._auto_arrange_on_reload:
            # Arranges the complete build plate after reloading a file. Can be set on/off in the settings.
            Application.getInstance().arrangeAll()
