from . import Blender, BLENDReader, BLENDWriter

from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog('uranium')
from UM.Mesh.MeshWriter import MeshWriter #For the binary mode flag.

def getMetaData():
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
    return {'extension': Blender.Blender(),
            'mesh_reader': BLENDReader.BLENDReader(),
            'mesh_writer': BLENDWriter.BLENDWriter()}
