# Imports from Uranium.
from UM.i18n import i18nCatalog
from UM.Mesh.MeshWriter import MeshWriter #For the binary mode flag.

# Imports from own package.
from . import Blender, BLENDReader, BLENDWriter


# The catalog used.
i18n_catalog = i18nCatalog('uranium')


## Initialization of the plugin.
def getMetaData():
    return {
        "tool": {
            "name": "Blender",
            "description": "Blender Tool",     # Displayed when hovering over the tool icon.
            "icon": "images/blender_logo.svg", # Icon displayed on the button.
            "tool_panel": "BlenderTool.qml",   # QML file used.
            "weight": 1
        },
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


## Registers the plugin in cura on start.
def register(app):
    return {'tool': Blender.Blender(),
            'mesh_reader': BLENDReader.BLENDReader(),
            'mesh_writer': BLENDWriter.BLENDWriter()}
