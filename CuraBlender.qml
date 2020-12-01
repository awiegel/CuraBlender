// Imports the standard GUI elements from QTQuick.
import QtQuick 2.10
import QtQuick.Controls 1.4

// Imports the Uranium GUI elements, which are themed for Cura.
import UM 1.5 as UM

// Imports the Cura GUI elements.
import Cura 1.6 as Cura


// Dialog from Uranium.
UM.Dialog
{
    // Everything needs an id to be adressed elsewhere in the file.
    id: base

    // The title of the window.
    title: catalog.i18nc("@title:window", "CuraBlender Settings")

    // We don't want the dialog to block input in the main window.
    modality: Qt.NonModal

    // Setting the dimensions of the dialog window and prohibiting resizing.
    width: minimumWidth
    minimumWidth: 350
    height: minimumHeight
    minimumHeight: 250

    // Main component. Contains functions and smaller components like buttons and checkboxes.
    Item
    {
        id: settings
        width: base.width
        height: base.height
        UM.I18nCatalog { id: catalog; name: "cura"}

        readonly property string stlImportType: "stl"
        readonly property string objImportType: "obj"
        readonly property string x3dImportType: "x3d"
        readonly property string plyImportType: "ply"

        // Gets the first state of the import type. Calls getImportType function and loads the attribute from the settings file.
        property var currentImportType: UM.Preferences.getValue("cura_blender/file_extension")

        // Updates the view every time the currentImportType changes.
        onCurrentImportTypeChanged:
        {
            var type = currentImportType

            // Sets checked state of import type buttons.
            stlButton.checked = type === stlImportType
            objButton.checked = type === objImportType
            x3dButton.checked = type === x3dImportType
            plyButton.checked = type === plyImportType
        }

        // Only one file extension may be active at the same time.
        ExclusiveGroup
        {
            id: fileExtension
        }

        // Label above the import type selection.
        Label
        {
            id: importTypeLabel
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.topMargin: UM.Theme.getSize("default_margin").width
            height: UM.Theme.getSize("setting").height

            // The actual text.
            text: catalog.i18nc("@label", "Select Import Type")

            font: UM.Theme.getFont("medium_bold")
            color: UM.Theme.getColor("text")
        }

        // Sets import type to 'stl' button.
        Button
        {
            id: stlButton

            anchors.left: parent.left
            anchors.top: importTypeLabel.bottom
            style: UM.Theme.styles.tool_button
            property bool needBorder: true
            checkable: true
            exclusiveGroup: fileExtension

            // The path to the icon.
            iconSource: "images/stl_icon.svg"

            // The text when holding the mouse over the icon.
            text: catalog.i18nc("@action:button", ".stl")
            // Otherwise the text when holding the mouse over the icon would hide under the other icons.
            z: 4

            // Sets the current import type to 'stl' and unchecks every other box.
            onClicked: UM.Preferences.setValue("cura_blender/file_extension", settings.stlImportType)
        }

        // Sets import type to 'obj' button.
        Button
        {
            id: objButton

            anchors.left: stlButton.right
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            anchors.top: importTypeLabel.bottom
            style: UM.Theme.styles.tool_button
            property bool needBorder: true
            checkable: true
            exclusiveGroup: fileExtension

            // The path to the icon.
            iconSource: "images/obj_icon.svg"
            
            // The text when holding the mouse over the icon.
            text: catalog.i18nc("@action:button", ".obj")
            // Otherwise the text when holding the mouse over the icon would hide under the other icons.
            z:3

            // Sets the current import type to 'obj' and unchecks every other box.
            onClicked: UM.Preferences.setValue("cura_blender/file_extension", settings.objImportType)
        }

        // Sets import type to 'x3d' button.
        Button
        {
            id: x3dButton

            anchors.left: objButton.right
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            anchors.top: importTypeLabel.bottom
            style: UM.Theme.styles.tool_button
            property bool needBorder: true
            checkable: true
            exclusiveGroup: fileExtension

            // The path to the icon.
            iconSource: "images/x3d_icon.svg"

            // The text when holding the mouse over the icon.
            text: catalog.i18nc("@action:button", ".x3d")
            // Otherwise the text when holding the mouse over the icon would hide under the other icons.
            z: 2

            // Sets the current import type to 'x3d' and unchecks every other box.
            onClicked: UM.Preferences.setValue("cura_blender/file_extension", settings.x3dImportType)
        }

        // Sets import type to 'ply' button.
        Button
        {
            id: plyButton

            anchors.left: x3dButton.right
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            anchors.top: importTypeLabel.bottom
            style: UM.Theme.styles.tool_button
            property bool needBorder: true
            checkable: true
            exclusiveGroup: fileExtension

            // The path to the icon.
            iconSource: "images/ply_icon.svg"
            
            // The text when holding the mouse over the icon.
            text: catalog.i18nc("@action:button", ".ply")
            // Otherwise the text when holding the mouse over the icon would hide under the other icons.
            z: 1

            // Sets the current import type to 'ply' and unchecks every other box.
            onClicked: UM.Preferences.setValue("cura_blender/file_extension", settings.plyImportType)
        }

        // CuraBlender logo.
        UM.RecolorImage
        {
            id: logoLabel
            anchors.left: plyButton.right
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            anchors.top: importTypeLabel.bottom

            // The path to the logo.
            source: "images/CuraBlender_logo.svg"

            width: plyButton.width
            height: plyButton.height
            color: UM.Theme.getColor(source)
        }

        // Checkbox for live reload.
        Cura.CheckBoxWithTooltip
        {
            id: liveReloadCheckbox
            anchors.left: parent.left
            anchors.top: stlButton.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").width

            // The text for this checkbox.
            text: catalog.i18nc("@action:checkbox","Live Reload                                ")

            // The tooltip for this checkbox.
            tooltip: catalog.i18nc("@checkbox:description", "Automatically reloads the object inside cura on change.")

            // Calls getLiveReload and loads the entry state for live reload attribute.
            checked: UM.Preferences.getValue("cura_blender/live_reload")

            // Calls setLiveReload and sets the new state for live reload attribute.
            onClicked: UM.Preferences.setValue("cura_blender/live_reload", checked)
        }

        // Checkbox for auto arrange on reload.
        Cura.CheckBoxWithTooltip
        {
            id: autoArrangeOnReloadCheckbox
            anchors.left: parent.left
            anchors.top: liveReloadCheckbox.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").width

            // The text for this checkbox.
            text: catalog.i18nc("@action:checkbox","Auto Arrange on reload          ")

            // The tooltip for this checkbox.
            tooltip: catalog.i18nc("@checkbox:description", "Auto arranges the complete build plate after 'Live Reload'.")

            // Calls getAutoArrangeOnReload and loads the entry state for auto arrange on reload attribute.
            checked: UM.Preferences.getValue("cura_blender/auto_arrange_on_reload")

            // Calls setAutoArrangeOnReload and sets the new state for auto arrange on reload attribute.
            onClicked: UM.Preferences.setValue("cura_blender/auto_arrange_on_reload", checked)
        }

        // Checkbox for auto scale on read.
        Cura.CheckBoxWithTooltip
        {
            id: autoScaleOnReadCheckbox
            anchors.left: liveReloadCheckbox.right
            anchors.top: stlButton.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").width

            // The text for this checkbox.
            text: catalog.i18nc("@action:checkbox","Auto Scale on read")

            // The tooltip for this checkbox.
            tooltip: catalog.i18nc("@checkbox:description", "Scales object to fit the build plate.")

            // Calls getAutoScaleOnRead and loads the entry state for auto scale on read attribute.
            checked: UM.Preferences.getValue("cura_blender/auto_scale_on_read")

            // Calls setAutoScaleOnRead and sets the new state for auto scale on read attribute.
            onClicked: UM.Preferences.setValue("cura_blender/auto_scale_on_read", checked)
        }

        // Checkbox for show scale message.
        Cura.CheckBoxWithTooltip
        {
            id: showScaleMessageCheckbox
            anchors.left: autoArrangeOnReloadCheckbox.right
            anchors.top: autoScaleOnReadCheckbox.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").width

            // The text for this checkbox.
            text: catalog.i18nc("@action:checkbox","Show Scale Message")

            // The tooltip for this checkbox.
            tooltip: catalog.i18nc("@checkbox:description", "Shows or hides the auto scale message.")

            // Calls getShowScaleMessage and loads the entry state for show scale message attribute.
            checked: UM.Preferences.getValue("cura_blender/show_scale_message")

            // Calls setShowScaleMessage and sets the new state for show scale message attribute.
            onClicked: UM.Preferences.setValue("cura_blender/show_scale_message", checked)
        }

        // Checkbox for show scale message.
        Cura.CheckBoxWithTooltip
        {
            id: showCloseBlenderInstancesWarning
            anchors.left: parent.left
            anchors.top: autoArrangeOnReloadCheckbox.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").width

            // The text for this checkbox.
            text: catalog.i18nc("@action:checkbox","Warn before closing other Blender instances (Caution!)")

            // The tooltip for this checkbox.
            tooltip: catalog.i18nc("@checkbox:description", "Potential loss of data. Deactivate on own risk.")

            // Calls getShowCloseBlenderInstancesWarning and loads the entry state for show close blender instances warning attribute.
            checked: UM.Preferences.getValue("cura_blender/warn_before_closing_other_blender_instances")

            // Calls setShowCloseBlenderInstancesWarning and sets the new state for show close blender instances warning attribute.
            onClicked: UM.Preferences.setValue("cura_blender/warn_before_closing_other_blender_instances", checked)
        }

        // Help button.
        Cura.SecondaryButton
        {
            id: helpButton
            anchors.right: parent.right
            anchors.rightMargin: UM.Theme.getSize("default_margin").width
            anchors.top: parent.top
            height: UM.Theme.getSize("setting_control").height
            iconSource: UM.Theme.getIcon("external_link")

            // The graphical representation of this object inside cura.
            text: catalog.i18nc("@action:button", "Help")

            // Opens the help URL with web browser.
            onClicked:
            {
                const url = "https://github.com/awiegel/CuraBlender"
                Qt.openUrlExternally(url)
            }
        }
    }
}
