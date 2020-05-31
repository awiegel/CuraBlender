import subprocess
import os.path
import platform
import glob

from UM.Logger import Logger
from UM.Message import Message
from UM.Extension import Extension
from UM.Scene.Selection import Selection
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Application import Application
from cura.Scene.CuraSceneNode import CuraSceneNode
from UM.i18n import i18nCatalog

from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QUrl

from . import BLENDReader

i18n_catalog = i18nCatalog('uranium')


global blender_path, file_extension
blender_path = None
file_extension = 'stl'


class Blender(Extension):
    global blender_path
    def __init__(self):
        super().__init__()
        self._supported_extensions = ['.blend']

        self.setMenuName(i18n_catalog.i18nc('@item:inmenu', 'Blender'))
        self.addMenuItem(i18n_catalog.i18nc('@item:inmenu', 'Open in Blender'), self.openInBlender)
        self.addMenuItem(i18n_catalog.i18nc('@item:inmenu', 'File Extension'), self.file_extension)


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
        blender_path = ''.join(dialog.selectedFiles())
        return blender_path


    def openInBlender(self):
        if len(Selection.getAllSelectedObjects()) == 0:
           message = Message(text=i18n_catalog.i18nc('@info','Select Object first'), title=i18n_catalog.i18nc('@info:title', 'Please select the object you want to open.'))
           message._lifetime = 10
           message.show()
        else:
           for selection in Selection.getAllSelectedObjects():
               file_path = selection.getMeshData().getFileName()
               self.openBlender(file_path)


    def openBlender(self, file_path):
        if blender_path is None:
            QDesktopServices.openUrl(QUrl('https://www.blender.org/download/'))
        else:
            current_file_extension = os.path.basename(file_path).partition('.')[2]

            if current_file_extension == 'blend':
                if '_curasplit_' not in file_path:
                    subprocess.run((blender_path, file_path), shell = True)
                else:
                    index = int(file_path[file_path.index('_curasplit_') + 11:][:-6]) - 1
                    file_path = '{}.blend'.format(file_path[:file_path.index('_curasplit_')])
                    open_file = 'bpy.ops.wm.open_mainfile()'

                    command = BLENDReader.BLENDReader.buildCommand(file_path, 'Multiple nodes', open_file, str(index), background = False)
                    subprocess.run(command, shell = True)

            else:
                execute_list = 'bpy.data.objects.remove(bpy.data.objects["Cube"]);'
                if current_file_extension == 'stl' or current_file_extension == 'ply':
                    execute_list = execute_list + 'bpy.ops.import_mesh.{}(filepath = "{}");'.format(current_file_extension, file_path)
                elif current_file_extension == 'obj' or current_file_extension == 'x3d':
                    execute_list = execute_list + 'bpy.ops.import_scene.{}(filepath = "{}");'.format(current_file_extension, file_path)
                else:
                    export_file = None

                export_file = '{}/cura_temp.blend'.format(os.path.dirname(file_path))

                execute_list = execute_list + 'bpy.ops.wm.save_as_mainfile(filepath = "{}")'.format(export_file)
                Logger.log('d', execute_list)
                Logger.log('d', export_file)
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

                subprocess.run((blender_path, export_file), shell = True)
                os.remove(export_file)


    def _openBlenderTrigger(self, message, action):
        if action == 'Open in Blender':
            self.openInBlender()
        elif action == 'Ignore':
            message.hide()
        else:
            None


    def file_extension(self):
        message = Message(text=i18n_catalog.i18nc('@info','File Extension'), title=i18n_catalog.i18nc('@info:title', 'Choose your File Extension.'))
        message._lifetime = 15
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
