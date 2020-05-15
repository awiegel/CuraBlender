import os.path

from UM.Logger import Logger
from UM.Mesh.MeshReader import MeshReader


class BLENDReader(MeshReader):
    def __init__(self) -> None:
        super().__init__()
        self._supported_extensions = [".blend"]
        self._namespaces = {}   # type: Dict[str, str]

    # Main entry point
    # Reads the file, returns a SceneNode (possibly with nested ones), or None
    def _read(self, file_name):
        base_name = os.path.basename(file_name)
