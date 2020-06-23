# Blender
This Plugin provides support for reading/writing BLEND files directly without importing/exporting.
It also offers extra features that are described in this document.

## Table of contents
- [1. Installation](#1-installation)
- [2. Functionality](#2-functionality)
- [3. Explanation of all files](#3-explanation-of-all-files)
- [4. Potential problems](#4-potential-problems)

## 1. Installation
To install this plugin simply drag this folder unzipped into your plugins folder.

The following tools are needed for this plugin to work:
* Blender (https://www.blender.org/download/)
* Python  (https://www.python.org/downloads/)


## 2. Functionality
Default functionality:
* **BLENDReader:** Provides support for reading BLEND files.
* **BLENDWriter:** Provides support for writing BLEND files. The objects inside the BLEND file are evenly distributed along the x-axis.

Functionality accessed through the toolbar:
* **Open in Blender:** Opens the currently selected object in blender.
* **Select Import Type:** Blender files get converted into another file type on reading/writing. Select one of four types for this (stl, obj, x3d, ply).

Functions that can be turned on/off:
* **Live Reload:** Changing a loaded object in blender and saving it, automatically reloads the object inside cura.
* **Auto arrange on reload:** After an object gets reloaded through the 'Live Reload' function, auto arranges the complete build plate.
* **Auto scale on read:** If object is either too big or too small, scales it down/up automatically to fit the build plate.
* **Show scale message:** Shows or hides the auto scale message.


## 3. Explanation of all files
**Blender.py**
The main module of this plugin. Contains the tool and general functions.
Functions:
* Loading and writing the settings file.
* Setting and verifying the path to blender.
* Opening files in blender.
* File watcher for BLEND and foreign files for the 'Live Reload' function.

**BLENDReader.py**
The reader module of this plugin. Provides support for reading BLEND files.
Processes the file with the help of the BlenderAPI module. Counts the number of objects inside the file and reads them independently from each other.
Gives files with multiple objects a special postfix (_curasplit_{index}) for reloading the correct object later.

**BLENDWriter.py**
The writer module of this plugin. Provides support for writing BLEND files.
Gets all files on the current build plate and saves them to a new BLEND file. Also works for split objects from BLEND files and foreign files (stl, obj, x3d, ply).

**BlenderAPI.py**
The interface module between cura and blender. Uses the blender python API to work with blender objects.
Contains four different program modes:
* **Count nodes:** Gets called everytime before reading loading the actual objects. Counts the number of objects inside the file and decides which mode to use.
* **Single node:** Gets called when file only contains one object. Removes decorators and loads the object.
* **Multiple nodes:** Gets called when file contains multiple objects. Removes decorators and loads the object based on given index. This program gets called for every object inside the file.
* **Write:** Gets called on writing to a blender file. Loads objects from BLEND files based on index and imports foreign files. 

**__init__.py**
Registers the tool, the mesh reader and the mesh writer inside cura on startup.

**BlenderTool.qml**
Builds the tool. Contains all information about icons, buttons and checkboxes.

**blender_settings.json**
Settings that gets loaded on startup.
To save/write to this file with this plugin, the user needs to give permission (only if inside a protected path). Either modify the files properties to enable write mode or execute cura as administrator. 
Quick tip: Execute cura as administrator on the first time using this plugin and set the desired settings. It's also possible to modify this file manually.

Settings:
Blender path: The blender path inside this settings file gets set automatically or by user with the help of the file explorer when the plugin cannot find it.

Accessed via the tool interface there are several settings the user can choose.
Live Reload:
Auto Arrange on Reload:
Auto Scale on Read:
Show Scale Message:

**plugin.json**
Contains some information about the plugin.

**images**
Icons used by the tool interface.

**.gitignore**
A file used by git to ignore selected files on commiting.

**README.md**
This file. Contains documentation about the plugin.

**LICENSE**
A license file.

## 4. Potential problems
**Platform Support**
This plugin should work on every platform including **Windows**, **MacOS** and **Linux**.
Only tested on Windows so far. Pathing could be bugged on MacOS and Linux.

**Blender Version**
Because this plugin closely works with Blender and it's python API, there could occur problems with new Blender updates.
