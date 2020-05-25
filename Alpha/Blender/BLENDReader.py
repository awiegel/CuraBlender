import sys
import platform
import os.path
import glob
import subprocess

from UM.Logger import Logger
from UM.Message import Message
from UM.Application import Application
from UM.Mesh.MeshReader import MeshReader

from PyQt5.QtWidgets import QFileDialog
from UM.i18n import i18nCatalog

i18n_catalog = i18nCatalog('uranium')


global global_path, blender_path
global_path = None
blender_path = None

class BLENDReader(MeshReader):
    def __init__(self) -> None:
        super().__init__()
        self._supported_extensions = ['.blend']


    # Main entry point
    # Reads the file, returns a SceneNode (possibly with nested ones), or None
    def read(self, file_path):
        global global_path, blender_path
        system = platform.system()

        if not blender_path:
            blender_path = self._setBlenderPath(blender_path, system)
        
        if not os.path.exists(blender_path):
            blender_path = self._openFileDialog(blender_path, system)

        global_path = file_path
        temp_path = self._convertFile(blender_path, file_path)
        data = self._openFile(temp_path)
        return data


    def _setBlenderPath(self, blender_path, system):
        if system == 'Windows':
            temp_blender_path = glob.glob('C:/Program Files/Blender Foundation/**/*.exe')
            blender_path = ''.join(temp_blender_path).replace('\\', '/')
            #blender_path = 'test'
        elif system == 'Darwin':
            blender_path = '/Applications/Blender.app/Contents/MacOS/blender'
        elif system == 'Linux':
            blender_path = '/usr/share/blender/2.82/blender'
        else:
            blender_path = None
        return blender_path


    def _openFileDialog(self, blender_path, system):
        message = Message(text=i18n_catalog.i18nc('@info', 'Set your blender path manually'), title=i18n_catalog.i18nc('@info:title', 'Blender not found'))
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


    def _convertFile(self, blender_path, file_path):
        temp_path = os.path.dirname(file_path) + '/temp.stl'
        command = (
            blender_path,
            file_path,
            '--background',
            '--python-expr',
            'import bpy;'
            'import sys;'
            'temp_path = sys.argv[-1];'
            'bpy.ops.export_mesh.stl(filepath = temp_path, check_existing = False, global_scale = 10)',
            '--', temp_path
        )
        command = subprocess.Popen(command, shell = True)
        command.wait()
        return temp_path


    def _openFile(self, temp_path):
        reader = Application.getInstance().getMeshFileHandler().getReaderForFile(temp_path)
        data = reader.read(temp_path)
        #os.remove(temp_path)
        return data
