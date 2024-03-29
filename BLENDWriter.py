"""Meshwriter for .blend files."""

# Imports from the python standard library.
import os
import subprocess

# Imports from Uranium.
from UM.Mesh.MeshWriter import MeshWriter
from UM.Logger import Logger
from UM.Application import Application

# Imports from Cura.
from cura.Scene.CuraSceneNode import CuraSceneNode

# Imports from own package.
from CuraBlender import CuraBlender
from CuraBlender.DeprecatedVersionCheck import DEPRECATED_VERSION

# Imports from QT.
if not DEPRECATED_VERSION:
    from PyQt6.QtCore import QFileSystemWatcher
else:
    from PyQt5.QtCore import QFileSystemWatcher


class BLENDWriter(MeshWriter):
    """A MeshWriter subclass that performs .blend file saving."""

    def __init__(self):
        """The constructor, which calls the super-class-contructor (MeshWriter).

        Adds a filewatcher to replace the saved file from the writer job by our own generated file.
        """

        super().__init__(add_to_recent_files = False)

        self._write_watcher = QFileSystemWatcher()
        self._write_watcher.fileChanged.connect(self._write_changed)

        self._plugin_path = None
        self._script_path = None
        self._blender_path = None


    def write(self, stream, nodes, mode = MeshWriter.OutputMode.BinaryMode):
        """Main entry point for writing the file.

        :param stream: Buffer containing new file name and more.
        :param nodes: All nodes on the current scene.
        :param mode: The mode we write our file in. Not important here.
        :return: Always true, because the actual writing happens internal and not in this job.
        """

        # The return value: The status either successful or unsuccessful.
        success = True

        # Checks if path to blender is correct.
        if CuraBlender.CuraBlender.verify_blender_path(manual=False):

            self._plugin_path = CuraBlender.CuraBlender.get_plugin_path()
            self._script_path = os.path.join(self._plugin_path, 'BlenderAPI.py')

            file_list = self._create_file_list(nodes)

            (blender_files, execute_list) = self._create_execute_list(file_list)

            command = self._build_command('Write', stream.name, blender_files, execute_list, temp_path = None)

            subprocess.Popen(command, shell = True)

            self._write_watcher.addPath(stream.name)
        else:
            # Failure message already gets called at other place.
            Logger.logException('e', 'Problems with path to blender!')
            success = False

        return success


    def _create_execute_list(self, file_list):
        """Creates a list (String) with instructions for every file in the file list.

        :param file_list: File list with paths of nodes.
        :return: A list (String) with all files with the .blend extension.
        :return: A list (String) with all files with different file extensions.
        """

        blender_files = set()
        execute_list = ''
        # Checks the file extension and builds the command based on it.
        for file_path in file_list:
            if file_path.endswith('.blend'):
                if '_curasplit_' in file_path:
                    file_path = '{}.blend'.format(file_path[:file_path.index('_curasplit_')])
                blender_files.add(file_path)
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

        blend_list = ''
        processes = []
        for file_path in blender_files:
            temp_path = '{}_curatemp_.blend'.format(file_path[:-6])
            command = self._build_command('Write prepare', file_path, temp_path = temp_path)
            with subprocess.Popen(command, shell = True) as process:
                processes.append(process)
            blend_list = '{}{}_curatemp_.blend;'.format(blend_list, file_path[:-6])

        for process in processes:
            process.wait()

        return (blend_list, execute_list)


    def _build_command(self, program, file_name, blender_files = None, execute_list = None, temp_path = None):
        """Builds the command used by subprocess. Calls the 'Write' program.

        :param program: Mode used by the BlenderAPI to determine which program to run (set of instructions).
        :param file_name: The file name we selected when saving the file.
        :param blender_files: A list (String) with all blender files.
        :param execute_list: A list (String) with instructions for all other files.
        :param temp_path: A temporary path for converting the blend file and preparing the 'Write' step.
        :return: The complete command needed by subprocess.
        """

        self._blender_path = Application.getInstance().getPreferences().getValue('cura_blender/blender_path')
        if program == 'Write prepare':
            command = '"{}" "{}" --background --python "{}" -- "{}" "{}"'.format(self._blender_path, file_name, self._script_path, temp_path, program)
        else:
            command = '"{}" --background --python "{}" -- "{}" "{}" "{}" "{}"'.format(self._blender_path, self._script_path, file_name, execute_list, blender_files, program)
        return command


    @staticmethod
    def _create_file_list(nodes):
        """Creates a file list containing the file path of all nodes.

        :param nodes: All nodes on the current scene.
        :return: File list with all paths of real nodes.
        """

        file_list = []
        for node in nodes:
            for children in node.getAllChildren():
                # Filters nodes without real meshdata and which doesn't belong to any file.
                if isinstance(children, CuraSceneNode) and not children.callDecoration("isGroup") and children.getMeshData().getFileName():
                    file_list.append(children.getMeshData().getFileName())
        return file_list


    @staticmethod
    def _write_changed(path):
        """On file changed connection. Deletes the original saved file and replaces it with our own generated one.

        :param path: The path of our file we try to save.
        """

        # Instead of overwriting files, blender saves the old one with .blend1 extension. This file is corrupted, so we delete it.
        if os.path.isfile(path + '1'):
            os.remove(path + '1')
