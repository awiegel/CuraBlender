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



class BLENDWriter(MeshWriter):
    def __init__(self):
        super().__init__(add_to_recent_files = False)
        #self._supported_extensions = ['.blend']


    # Main entry point
    # Reads the file, returns a SceneNode (possibly with nested ones), or None
    def write(self, stream, nodes, mode = MeshWriter.OutputMode.BinaryMode):
        Logger.log('d', 'TEST')
        Logger.log('d', stream)
        Logger.log('d', stream.name)
        Logger.log('d', nodes)
        for node in nodes:
            Logger.log('d', node)
        #for atr in dir(stream):
        #    Logger.log('d', '%s, %s',atr, getattr(stream, atr))
        #Logger.log('d', nodes)
        #for atr in dir(nodes):
        #    Logger.log('d', '%s, %s',atr, getattr(nodes, atr))
        file_list = []

        for node in nodes:
            for children in node.getAllChildren():
                if isinstance(children, CuraSceneNode) and children.getMeshData().getFileName() is not None:
                    file_list.append(children.getMeshData().getFileName())
                    Logger.log('d', file_list)
        
        execute_list = 'bpy.data.objects.remove(bpy.data.objects["Cube"]);'
        #temp_list.append('bpy.data.objects.remove(bpy.data.objects["Cube"])')
        for x in file_list:
            Logger.log('d', x)
            if x.endswith('.stl'):
                Logger.log('d', 'LOLOLOL')
                execute_list = execute_list + 'bpy.ops.import_mesh.stl(filepath = "{}");'.format(x)

        #temp_list.append('bpy.ops.wm.save_as_mainfile(filepath = "C:/Users/alex-/Documents/f.blend")')
        execute_list = execute_list + 'bpy.ops.wm.save_as_mainfile(filepath = "C:/Users/alex-/Documents/f.blend")'
        #stl_path
        Logger.log('d', stream.name)
        Logger.log('d', execute_list)
        #blend_path = stream.name
        blender_path = 'C:/Program Files/Blender Foundation/Blender 2.82/blender.exe'
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
        #sys.exit()

            #for atr in dir(node):
            #    Logger.log('d', '%s, %s',atr, getattr(node, atr))
            #Logger.log('d', node.getName())
            #Logger.log('d', node.getAllChildren())
                #Logger.log('d', x)
                    #Logger.log('d', x.getName())
                    #for atr in dir(x.getMeshData()):
                    #    Logger.log('d', '%s, %s',atr, getattr(x.getMeshData(), atr))
                    #for atr in dir(x.getChildren()):
        #for atr in dir(nodes.getMeshData()):
        #    Logger.log('d', '%s, %s',atr, getattr(nodes.getMeshData(), atr))

