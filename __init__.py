# Imports from Uranium.
from UM.Mesh.MeshWriter import MeshWriter # For the binary mode flag.

# Imports from own package.
from . import CuraBlender, BLENDReader, BLENDWriter


def getMetaData():
    """Initialization of the plugin."""

    return {
        'type': 'extension',
        'mesh_reader': [
            {
                'extension': 'blend',
                'description': CuraBlender.catalog.i18nc('@item:inlistbox', 'BLEND File')
            }
        ],
        'mesh_writer': {
            "output": [
                {
                    "mode": MeshWriter.OutputMode.BinaryMode,
                    "extension": "blend",
                    "description": CuraBlender.catalog.i18nc("@item:inlistbox", "BLEND File")
                }
            ]
        }
    }


def register(app):
    """Registers the plugin in cura on start."""

    return {
            'extension': CuraBlender.CuraBlender(),
            'mesh_reader': BLENDReader.BLENDReader(),
            'mesh_writer': BLENDWriter.BLENDWriter()
            }
