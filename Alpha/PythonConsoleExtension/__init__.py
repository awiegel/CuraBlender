from . import PythonConsole

from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("PythonConsole")

def getMetaData():
    return {
        "type": "extension",
        "plugin":
        {
            "name": "Python Console",
            "author": "Adrian Wagner",
            "version": "1.0.0",
            "supported_sdk_versions": ["6.0.0","6.1.0","6.2.0","6.3.0","7.0.0","7.1.0"],
            "description": i18n_catalog.i18nc("Description of plugin","Interact with Cura's source right in Cura itself.")
        }
    }

def register(app):
    return {"extension": PythonConsole.PythonConsole()}
