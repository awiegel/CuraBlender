import subprocess
import os.path
import platform
import glob
import time

from UM.Logger import Logger
from UM.Message import Message
from UM.Extension import Extension
from UM.Scene.Selection import Selection
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Application import Application
from cura.Scene.CuraSceneNode import CuraSceneNode
from UM.Mesh.ReadMeshJob import ReadMeshJob  # To reload a mesh when its file was changed.
from UM.i18n import i18nCatalog

from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QUrl, QFileSystemWatcher

from . import BLENDReader

i18n_catalog = i18nCatalog('uranium')


global blender_path, file_extension, fs_watcher
blender_path = None
file_extension = 'stl'
fs_watcher = QFileSystemWatcher()


class Blender(Extension):
    global blender_path, fs_watcher
    def __init__(self):
        super().__init__()
        self._supported_extensions = ['.blend']
        self._supported_foreign_extensions = ['stl', 'obj', 'x3d', 'ply']

        self.setMenuName(i18n_catalog.i18nc('@item:inmenu', 'Blender'))
        self.addMenuItem(i18n_catalog.i18nc('@item:inmenu', 'Open in Blender'), self.openInBlender)
        self.addMenuItem(i18n_catalog.i18nc('@item:inmenu', 'File Extension'), self.file_extension)

        fs_watcher.fileChanged.connect(self.fileChanged)
        self._foreign_file_watcher = QFileSystemWatcher()
        self._foreign_file_watcher.fileChanged.connect(self._foreignFileChanged)

    #@staticmethod
    #def getBlenderPath():
    #    return blender_path


    @classmethod
    def setBlenderPath(self):
        global blender_path
        system = platform.system()
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

        if not os.path.exists(blender_path):
            blender_path = self._openFileDialog(blender_path, system)


    @classmethod
    def _openFileDialog(self, blender_path, system):
        message = Message(text=i18n_catalog.i18nc('@info', 'Set your blender path manually'), title=i18n_catalog.i18nc('@info:title', 'Blender not found'))
        message._lifetime = 10
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
        else:
            message.hide()
            message = Message(text=i18n_catalog.i18nc('@info', 'No blender path was selected'), title=i18n_catalog.i18nc('@info:title', 'Blender not found'))
            message.show()

        blender_path = ''.join(dialog.selectedFiles())
        return blender_path


    def openInBlender(self):
        if blender_path is None:
            self.setBlenderPath()

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
            if len(open_files) == 1:
                self.openBlender(open_files.pop())
            else:                    
                message = Message(text=i18n_catalog.i18nc('@info','Select Object first'), title=i18n_catalog.i18nc('@info:title', 'Please select the object you want to open.'))
                message._lifetime = 10
                message.show()
        elif len(Selection.getAllSelectedObjects()) == 1:
            for selection in Selection.getAllSelectedObjects():
                file_path = selection.getMeshData().getFileName()
                if '_curasplit_' in file_path:
                    file_path = '{}.blend'.format(file_path[:file_path.index('_curasplit_')])
                self.openBlender(file_path)
        else:
            files = set()
            for selection in Selection.getAllSelectedObjects():
                file_path = selection.getMeshData().getFileName()
                if '_curasplit_' in file_path:
                    file_path = '{}.blend'.format(file_path[:file_path.index('_curasplit_')])
                files.add(file_path)
            if len(files) == 1:
                self.openBlender(file_path)
            else:
                message = Message(text=i18n_catalog.i18nc('@info','Please rethink your selection.'), title=i18n_catalog.i18nc('@info:title', 'Select only objects from same file'))
                message._lifetime = 10
                message.show()


    def openBlender(self, file_path):
        if blender_path is None:
            QDesktopServices.openUrl(QUrl('https://www.blender.org/download/'))
        else:
            current_file_extension = os.path.basename(file_path).partition('.')[2]

            if current_file_extension == 'blend':
                if '_curasplit_' in file_path:
                    file_path = '{}.blend'.format(file_path[:file_path.index('_curasplit_')])
                subprocess.Popen((blender_path, file_path), shell = True)

            else:
                execute_list = 'bpy.data.objects.remove(bpy.data.objects["Cube"]);'
                if current_file_extension == 'stl' or current_file_extension == 'ply':
                    execute_list = execute_list + 'bpy.ops.import_mesh.{}(filepath = "{}");'.format(current_file_extension, file_path)
                elif current_file_extension == 'obj' or current_file_extension == 'x3d':
                    execute_list = execute_list + 'bpy.ops.import_scene.{}(filepath = "{}");'.format(current_file_extension, file_path)
                else:
                    export_file = None

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
    

    def fileChanged(self, path):
        job = ReadMeshJob(path)
        job.finished.connect(self._readMeshFinished)
        job.start()


    def _readMeshFinished(self, job):
        job._nodes = []
        tempFlag = False
        for node in DepthFirstIterator(Application.getInstance().getController().getScene().getRoot()):
            if isinstance(node, CuraSceneNode) and node.getMeshData():
                file_path = node.getMeshData().getFileName()
                if '_curasplit_' in file_path:
                    file_path = '{}.blend'.format(file_path[:file_path.index('_curasplit_')])

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

        Application.getInstance().arrangeAll()
