import os.path
import subprocess
import sys

from UM.Logger import Logger
from UM.Application import Application
from UM.Mesh.MeshReader import MeshReader


class BLENDReader(MeshReader):
    def __init__(self) -> None:
        super().__init__()
        self._supported_extensions = ['.blend']
        self._namespaces = {}   # type: Dict[str, str]

    # Main entry point
    # Reads the file, returns a SceneNode (possibly with nested ones), or None
    def _read(self, file_path):
        temp_path = os.path.dirname(file_path) + '/temp.stl'
        blender_path = 'C:/Program Files/Blender Foundation/Blender 2.82/blender.exe'

        command = (
            blender_path,
            file_path,
            '--background',
            '--python-expr',
            'import bpy;'
            'import sys;'
            'stl_path = sys.argv[-1];'
            'bpy.ops.export_mesh.stl(filepath = stl_path, check_existing = False, global_scale = 10)',
            '--', temp_path
        )
        command = subprocess.Popen(command)
        command.wait()

        reader = Application.getInstance().getMeshFileHandler().getReaderForFile(temp_path)
        data = reader.read(temp_path)
        os.remove(temp_path)
        return data
