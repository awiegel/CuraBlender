from . import Blender, BLENDReader

from UM.i18n import i18nCatalog
catalog = i18nCatalog("uranium")


def getMetaData():
    return {
        "type": "extension",
        "mesh_reader": [
            {
                "extension": "blend",
                "description": catalog.i18nc("@item:inlistbox", "BLEND File")
            }
        ]
    }


def register(app):
    return {"extension": Blender.Blender(),
            "mesh_reader": BLENDReader.BLENDReader()}
