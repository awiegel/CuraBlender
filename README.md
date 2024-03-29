# CuraBlender Manual <img align="right" width="10%" height="10%" src="Documentation/images/CuraBlender_logo.png" />
This is a plugin for ultimaker cura which integrates blender for a much better workflow.

<br/>

## Table of contents
- [1. Trailer](#1-Trailer)
- [2. Installation](#2-Installation)
- [3. Functionality / Usage](#3-Functionality--Usage)
- [4. Suggestions / Bug reports](#4-Suggestions--Bug-reports)

<br/> <br/> <br/>

## 1. Trailer

[![CuraBlender](https://img.youtube.com/vi/0cdlJtuJI70/0.jpg)](https://www.youtube.com/watch?v=0cdlJtuJI70)

**Note:** This plugin changed from tool to extension. It's now accessible through the extensions tab.

<div class="page"/> <br/> <br/> <br/>

## 2. Installation
To install this plugin, simply download it from the [Ultimaker Marketplace](https://marketplace.ultimaker.com/app/cura/plugins/awiegel/CuraBlender).

The following tool is needed for this plugin to work:
* **Blender** (https://www.blender.org/download/) (**2.80 or higher** is required)

<br/> <br/> <br/>

## 3. Functionality / Usage
**Default functionality:**
* **BLENDReader:** Provides support for reading BLEND files. \
To open a BLEND file, simply press on `Open file(s)` or drag the desired file into the cura window.
If it's the first use time, the plugin tries to find the path to blender. If not successful, a file explorer window will open up, where the user can set the path to blender manually.
If the BLEND file contains multiple objects, all objects will be loaded separately.

* **BLENDWriter:** Provides support for writing BLEND files. The objects inside the BLEND file are evenly distributed along the x-axis. \
To save the current build plate in a BLEND file, press `Slice` on the bottom right corner and then `Save to File`.
Objects can be single objects (one object per BLEND file) or multiple objects (multiple objects per BLEND file).
The user can also load a BLEND file with multiple objects and delete some. Only the objects remained on the current build plate will be written to the BLEND file.
Foreign files (stl, obj, x3d, ply) can also be written to a BLEND file.
Any combination of those objects/files will work.

<div class="page"/> <br/>

**Functionality accessed through the extensions tab:**  

To use the extension of this plugin, click on the extensions tab and search for CuraBlender. \
There are multiple options available:
* **Open in Blender:**
Opens the currently selected object in blender and also creates a file watcher for this file.
If the object inside blender will be changed and saved, cura automatically updates the corresponding object in cura.
Groups cannot be opened due to how file reference works.

* **Settings:**
    * **Select Import Type:** Blender files get converted into another file type on reading/writing. Select one of four types for this (stl, obj, x3d, ply).
    * **Help:** Forwards the user to the official [GitHub](https://github.com/awiegel/CuraBlender) page of this plugin.
    * **Functions that can be turned on/off:**
        <img align="right" width="50%" height="50%" src="Documentation/images/CuraBlender_interface.png" />
        * **Live Reload:** Changing a loaded object in blender and saving it, automatically reloads the object inside cura.
        * **Auto arrange on reload:** After an object gets reloaded through the 'Live Reload' function, auto arranges the complete build plate.
        * **Auto scale on read:** If object is either too big or too small, scales it down/up automatically to fit the build plate.
        * **Show scale message:** Shows or hides the auto scale message.
        * **Warn before closing other Blender instances (Caution!):** Shows or hides the message for closing other blender instances when opening a new one. Potential loss of data. Deactivate on own risk.

* **Debug Blenderpath:** Allows the user to set the path to blender manually. This can be used to select different versions of blender or debug the path on problems.

All settings are saved inside a cura specific folder with the preferences module from Uranium.
Changing settings inside the settings window will permanently save those settings inside the settings file.
The next time the user starts cura, those settings will be loaded.

<br/> <br/> <br/>

## 4. Suggestions / Bug reports
If you encounter any problems while using this plugin or have any suggestions or feedback, \
feel free to contact me. \
Read the [Known challenges](Documentation/README.md/#5-Known-challenges) section in the [documentation](Documentation/README.md) first for a listing of all problems and suggestions.
