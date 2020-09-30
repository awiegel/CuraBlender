# Imports from Uranium.
from UM.i18n import i18nCatalog
from UM.Mesh.MeshWriter import MeshWriter # For the binary mode flag.

# Imports from own package.
from . import Blender, BLENDReader, BLENDWriter


# The catalog used.
i18n_catalog = i18nCatalog('uranium')


def getMetaData():
    """Initialization of the plugin."""

    return {
        'type': 'extension',
        'mesh_reader': [
            {
                'extension': 'blend',
                'description': i18n_catalog.i18nc('@item:inlistbox', 'BLEND File')
            }
        ],
        'mesh_writer': {
            "output": [
                {
                    "mode": MeshWriter.OutputMode.BinaryMode,
                    "extension": "blend",
                    "description": i18n_catalog.i18nc("@item:inlistbox", "BLEND File")
                }
            ]
        }
    }


def register(app):
    """Registers the plugin in cura on start."""

    return {
            'extension': Blender.Blender(),
            'mesh_reader': BLENDReader.BLENDReader(),
            'mesh_writer': BLENDWriter.BLENDWriter()
            }
