# Imports from Uranium.
from UM.Application import Application
from UM.Version import Version


DEPRECATED_VERSION = Application.getInstance().getAPIVersion() < Version("8.0.0")
