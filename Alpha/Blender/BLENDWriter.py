import sys
import platform
import os.path
import glob
import subprocess


from UM.Logger import Logger
from UM.Message import Message
from UM.Application import Application
from UM.Mesh.MeshWriter import MeshWriter
from UM.i18n import i18nCatalog

from UM.Job import Job
from cura.Scene.CuraSceneNode import CuraSceneNode
i18n_catalog = i18nCatalog("cura")


from . import Blender
from . import BLENDReader

class BLENDWriter(MeshWriter):
    def __init__(self):
        super().__init__(add_to_recent_files = False)
        #self._supported_extensions = ['.blend']


    # Main entry point
    # Writes the file
    def write(self, stream, nodes, mode = MeshWriter.OutputMode.BinaryMode):
        if not Blender.blender_path:
            Blender.Blender.setBlenderPath()

        file_list = []

        for node in nodes:
            for children in node.getAllChildren():
                if isinstance(children, CuraSceneNode) and children.getMeshData().getFileName() is not None:
                    file_list.append(children.getMeshData().getFileName())
                    Logger.log('d', file_list)
        
        execute_list = ''
        blender_files = ''
        for file_path in file_list:
            if file_path.endswith('.blend'):
                blender_files = blender_files + file_path + ';'
            elif file_path.endswith('.stl'):
                execute_list = execute_list + 'bpy.ops.import_mesh.stl(filepath = "{}");'.format(file_path)
            elif file_path.endswith('.ply'):
                execute_list = execute_list + 'bpy.ops.import_mesh.ply(filepath = "{}");'.format(file_path)
            elif file_path.endswith('.obj'):
                execute_list = execute_list + 'bpy.ops.import_scene.obj(filepath = "{}");'.format(file_path)
            elif file_path.endswith('.x3d'):
                execute_list = execute_list + 'bpy.ops.import_scene.x3d(filepath = "{}");'.format(file_path)
            else:
                None

        self._script_path = '{}/plugins/Blender/BlenderAPI.py'.format(os.getcwd())
        command = (
            Blender.blender_path,
            '--background',
            '--python',
            self._script_path,
            '--', stream.name, execute_list, blender_files, 'Write'
        )

        subprocess.Popen(command, shell = True)
        return True
