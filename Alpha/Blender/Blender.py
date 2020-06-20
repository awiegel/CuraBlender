# Imports from the python standard library.
import os
import platform
import glob
import time
import subprocess

# Imports from QT.
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QUrl, QFileSystemWatcher

# Imports from Uranium.
from UM.Logger import Logger
from UM.Message import Message
from UM.Extension import Extension
from UM.Scene.Selection import Selection
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Application import Application
from UM.Mesh.ReadMeshJob import ReadMeshJob  # To reload a mesh when its file was changed.
from UM.i18n import i18nCatalog

# Imports from Cura.
from cura.Scene.CuraSceneNode import CuraSceneNode


# The catalog used for showing messages.
i18n_catalog = i18nCatalog('uranium')


# Global variables used by our other modules.
global blender_path, file_extension, fs_watcher
blender_path = None
file_extension = 'stl'
fs_watcher = QFileSystemWatcher()


##  Main class for blender plugin.
class Blender(Extension):
    global blender_path, fs_watcher
    def __init__(self):
        ##  The constructor, which calls the super-class-contructor (MeshReader).
        ##  Adds .blend as a supported file extension.
        ##  Adds menu items and the filewatcher trigger function.
        super().__init__()
        self._supported_extensions = ['.blend']
        self._supported_foreign_extensions = ['stl', 'obj', 'x3d', 'ply']

        self.setMenuName(i18n_catalog.i18nc('@item:inmenu', 'Blender'))
        self.addMenuItem(i18n_catalog.i18nc('@item:inmenu', 'Open in Blender'), self.openInBlender)
        self.addMenuItem(i18n_catalog.i18nc('@item:inmenu', 'File Extension'), self.file_extension)

        fs_watcher.fileChanged.connect(self.fileChanged)
        self._foreign_file_watcher = QFileSystemWatcher()
        self._foreign_file_watcher.fileChanged.connect(self._foreignFileChanged)


    ##  Tries to set the path to blender automatically, if unsuccessful the user can set it manually.
    @classmethod
    def setBlenderPath(self):
        global blender_path
        system = platform.system()
        # Supports multi-platform
        if system == 'Windows':
            temp_blender_path = glob.glob('C:/Program Files/Blender Foundation/**/*.exe')
            blender_path = ''.join(temp_blender_path).replace('\\', '/')
            # blender_path = 'test'
        elif system == 'Darwin':
            blender_path = '/Applications/Blender.app/Contents/MacOS/blender'
        elif system == 'Linux':
            blender_path = '/usr/share/blender/2.82/blender'
        else:
            blender_path = None

        # If unsuccessful the user can set it manually.
        if not os.path.exists(blender_path):
            blender_path = self._openFileDialog(blender_path, system)


    ##  The user can set the path to blender manually. Gets called when blender isn't found in the expected place.
    #
    #   \param blender_path  The global path to blender to set it. Here it's either wrong or doesn't exist.
    #   \param system        The operating system from which the user operates.
    #   \return              The correctly set path to blender.
    @classmethod
    def _openFileDialog(self, blender_path, system):
        message = Message(text=i18n_catalog.i18nc('@info', 'Set your blender path manually'), title=i18n_catalog.i18nc('@info:title', 'Blender not found'))
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
            message = Message(text=i18n_catalog.i18nc('@info', 'No blender path was selected'), title=i18n_catalog.i18nc('@info:title', 'Blender not found'))
            message.show()

        blender_path = ''.join(dialog.selectedFiles())
        return blender_path


    ##  Checks if the selection of objects is correct and allowed and calls the actual function to open the file. 
    def openInBlender(self):
        # Checks if path for blender is set, otherwise tries to set it.
        if blender_path is None:
            self.setBlenderPath()

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
                message = Message(text=i18n_catalog.i18nc('@info','Select Object first'), title=i18n_catalog.i18nc('@info:title', 'Please select the object you want to open.'))
                message.show()
        # If one object is selecte, open it's file reference (file name)
        elif len(Selection.getAllSelectedObjects()) == 1:
            for selection in Selection.getAllSelectedObjects():
                file_path = selection.getMeshData().getFileName()
                if '_curasplit_' in file_path:
                    file_path = '{}.blend'.format(file_path[:file_path.index('_curasplit_')])
                self.openBlender(file_path)
        # If multiple objects are selected, check if they belong to more than one file.
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
                message = Message(text=i18n_catalog.i18nc('@info','Please rethink your selection.'), title=i18n_catalog.i18nc('@info:title', 'Select only objects from same file'))
                message.show()


    ##  Opens the given file in blender. File must not necessarily be a blender file.
    #
    #   \param file_path  The path of the file to open in blender.
    def openBlender(self, file_path):
        if blender_path is None:
            QDesktopServices.openUrl(QUrl('https://www.blender.org/download/'))
        else:
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
    ##  Explicit for foreign file types. (stl, obj, x3d, ply)
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


    ##  The user can choose in what file format the blender files should be converted to.
    def file_extension(self):
        message = Message(text=i18n_catalog.i18nc('@info','File Extension'), title=i18n_catalog.i18nc('@info:title', 'Choose your File Extension.'))
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


    ## The trigger function for the file_extension function.
    def _fileExtensionTrigger(self, message, action):
        global file_extension
        if action == 'stl':
            file_extension = 'stl'
        elif action == 'ply':
            file_extension = 'ply'
        elif action == 'x3d':
            file_extension = 'x3d'
        elif action == 'obj':
            file_extension = 'obj'
        else:
            None
    

    ##  On file changed connection. Rereads the changed file and updates it. This happens automatically and can be set on/off in the settings.
    #
    #   \param path  The path to the changed blender file.
    def fileChanged(self, path):
        job = ReadMeshJob(path)
        job.finished.connect(self._readMeshFinished)
        job.start()


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

        # Arranges the complete build plate after reloading a file. Can be on/off in the settings.
        Application.getInstance().arrangeAll()
