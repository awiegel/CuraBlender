# Imports from the python standard library.
import os
import subprocess

# Imports from QT.
from PyQt5.QtCore import QFileSystemWatcher

# Imports from Uranium.
from UM.Mesh.MeshWriter import MeshWriter
from UM.Logger import Logger

# Imports from Cura.
from cura.Scene.CuraSceneNode import CuraSceneNode

# Imports from own package.
from . import Blender


##  Writer class for .blend files.
class BLENDWriter(MeshWriter):
    ##  The constructor, which calls the super-class-contructor (MeshWriter).
    ##  Adds a filewatcher to replace the saved file from the writer job by our own generated file.
    def __init__(self):
        super().__init__(add_to_recent_files = False)

        self._write_watcher = QFileSystemWatcher()
        self._write_watcher.fileChanged.connect(self._writeChanged)


    ##  Main entry point for writing the file.
    #
    #   \param stream  Buffer containing new file name and more.
    #   \param nodes   All nodes on the current scene.
    #   \param mode    The mode we write our file in. Not important here.
    #   \return        Always true, because the actual writing happens internal and not in this job.
    def write(self, stream, nodes, mode = MeshWriter.OutputMode.BinaryMode):
        # Checks if path to this plugin is set.
        if not Blender.plugin_path:
            Blender.Blender.setPluginPath()
        # Checks if path to blender is set or if it's the correct path, otherwise tries to set it.
        if not Blender.verified_blender and (not Blender.blender_path or not Blender.Blender.verifyBlenderPath()):
            Blender.Blender.setBlenderPath()

        # The return value: The status either successful or unsuccessful.
        success = True

        # Only continues if correct path to blender is set.
        if Blender.verified_blender:
            file_list = self._createFileList(nodes)
            
            (blender_files, execute_list) = self._createExecuteList(file_list)

            command = self._buildCommand(stream.name, blender_files, execute_list)

            subprocess.Popen(command, shell = True)

            self._write_watcher.addPath(stream.name)
        else:
            # Failure message already gets called at other place.
            Logger.logException('e', 'Problems with path to blender!')
            success = False

        return success


    ##  Creates a file list containing the file path of all nodes.
    #
    #   \param nodes  All nodes on the current scene.
    #   \return       File list with all paths of real nodes.
    def _createFileList(self, nodes):
        file_list = []
        for node in nodes:
            for children in node.getAllChildren():
                # Filters nodes without real meshdata and which doesn't belong to any file.
                if isinstance(children, CuraSceneNode) and children.getMeshData().getFileName():
                    file_list.append(children.getMeshData().getFileName())
        return file_list


    ##  Creates a list (String) with instructions for every file in the file list.
    #
    #   \param file_list  File list with paths of nodes.
    #   \return           A list (String) with all files with the .blend extension.
    #   \return           A list (String) with all files with different file extensions.
    def _createExecuteList(self, file_list):
        blender_files = ''
        execute_list = ''
        # Checks the file extension and builds the command based on it.
        for file_path in file_list:
            if file_path.endswith('.blend'):
                blender_files = '{}{};'.format(blender_files, file_path)
            elif file_path.endswith('.stl'):
                execute_list = execute_list + "bpy.ops.import_mesh.stl(filepath = '{}');".format(file_path)
            elif file_path.endswith('.ply'):
                execute_list = execute_list + "bpy.ops.import_mesh.ply(filepath = '{}');".format(file_path)
            elif file_path.endswith('.obj'):
                execute_list = execute_list + "bpy.ops.import_scene.obj(filepath = '{}');".format(file_path)
            elif file_path.endswith('.x3d'):
                execute_list = execute_list + "bpy.ops.import_scene.x3d(filepath = '{}');".format(file_path)
            # Ignore objects with unsupported file extension.
            else:
                Logger.logException('e', '%s\nhas unsupported file extension and was ignored!', file_path)
        return (blender_files, execute_list)


    ##  Builds the command used by subprocess. Calls the 'Write' program.
    #
    #   \param file_name      The file name we selected when saving the file.
    #   \param blender_files  A list (String) with all blender files.
    #   \param execute_list   A list (String) with instructions for all other files.
    #   \return               The complete command needed by subprocess.
    def _buildCommand(self, file_name, blender_files, execute_list):
        self._script_path = os.path.join(Blender.plugin_path, 'BlenderAPI.py')
        command = '"{}" --background --python "{}" -- "{}" "{}" "{}" "{}"'.format(Blender.blender_path, self._script_path, file_name, execute_list, blender_files, 'Write')
        return command


    ##  On file changed connection. Deletes the original saved file and replaces it with our own generated one.
    #
    #   \param path  The path of our file we try to save.
    def _writeChanged(self, path):
        # Instead of overwriting files, blender saves the old one with .blend1 extension. This file is corrupted, so we delete it.
        if os.path.isfile(path + '1'):
            os.remove(path + '1')
