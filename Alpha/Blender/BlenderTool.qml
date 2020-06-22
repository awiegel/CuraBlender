// Import the standard GUI elements from QTQuick.
import QtQuick 2.10
import QtQuick.Controls 1.4

// Import the Uranium GUI elements, which are themed for Cura.
import UM 1.5 as UM

// Import the Cura GUI elements.
import Cura 1.6 as Cura

// Main component. Contains functions and smaller components like buttons and checkboxes.
Item
{
    id: base
    width: childrenRect.width
    height: childrenRect.height
    UM.I18nCatalog { id: catalog; name: "uranium"}

    readonly property string stlImportType: "stl"
    readonly property string objImportType: "obj"
    readonly property string x3dImportType: "x3d"
    readonly property string plyImportType: "ply"

    // Gets the first state of the import type. Calls getImportType function and loads the attribute from the settings file.
    property var currentImportType: UM.ActiveTool.properties.getValue("ImportType")

    // Updates the view every time the currentImportType changes
    onCurrentImportTypeChanged:
    {
        var type = currentImportType

        // Sets checked state of mesh type buttons.
        stlButton.checked = type === stlImportType
        objButton.checked = type === objImportType
        x3dButton.checked = type === x3dImportType
        plyButton.checked = type === plyImportType
    }
    
    // Function for the import type buttons.
    function setImportType(type)
    {
        // Calls setImportType function and sets current import type.
        UM.ActiveTool.setProperty("ImportType", type)
    }

    // Open in Blender button.
    Cura.PrimaryButton
    {
        id: openInBlenderButton
        anchors.left: parent.left
        anchors.top: parents.top
        height: UM.Theme.getSize("setting_control").height;

        // The graphical representation of this object inside cura.
        text: catalog.i18nc("@action:button", "Open in Blender");

        // Calls openInBlender function and opens the selected object in blender.
        onClicked: UM.ActiveTool.triggerAction("openInBlender");
    }

    // Label above our import type selection.
    Label
    {
        id: importTypeLabel
        anchors.top: openInBlenderButton.bottom;
        anchors.topMargin: UM.Theme.getSize("default_margin").width;
        height: UM.Theme.getSize("setting").height

        // The actual text.
        text: catalog.i18nc("@label", "Choose Import Type")

        font: UM.Theme.getFont("default")
        color: UM.Theme.getColor("text")
    }

    // Set import type to 'stl' button.
    Button
    {
        id: stlButton

        anchors.left: parent.left;
        anchors.top: importTypeLabel.bottom;
        style: UM.Theme.styles.tool_button;
        property bool needBorder: true
        checkable: true

        // The path to the icon.
        iconSource: "images/stl_icon.svg";

        // The text when holding the mouse over the icon.
        text: catalog.i18nc("@action:button", ".stl")
        // Otherwise the text when holding the mouse over the icon would hide under the other icons.
        z: 4

        // Sets the current import type to 'stl' and unchecks every other box.
        onClicked: setImportType(stlImportType)
    }
    
    // Set import type to 'obj' button.
    Button
    {
        id: objButton

        anchors.left: stlButton.right;
        anchors.leftMargin: UM.Theme.getSize("default_margin").width;
        anchors.top: importTypeLabel.bottom;
        style: UM.Theme.styles.tool_button;
        property bool needBorder: true
        checkable: true

        // The path to the icon.
        iconSource: "images/obj_icon.svg";
        
        // The text when holding the mouse over the icon.
        text: catalog.i18nc("@action:button", ".obj")
        // Otherwise the text when holding the mouse over the icon would hide under the other icons.
        z:3

        // Sets the current import type to 'obj' and unchecks every other box.
        onClicked: setImportType(objImportType)
    }

    // Set import type to 'x3d' button.
    Button
    {
        id: x3dButton

        anchors.left: objButton.right;
        anchors.leftMargin: UM.Theme.getSize("default_margin").width;
        anchors.top: importTypeLabel.bottom;
        style: UM.Theme.styles.tool_button;
        property bool needBorder: true
        checkable: true

        // The path to the icon.
        iconSource: "images/x3d_icon.svg";

        // The text when holding the mouse over the icon.
        text: catalog.i18nc("@action:button", ".x3d")
        // Otherwise the text when holding the mouse over the icon would hide under the other icons.
        z: 2

        // Sets the current import type to 'x3d' and unchecks every other box.
        onClicked: setImportType(x3dImportType)
    }

    // Set import type to 'ply' button.
    Button
    {
        id: plyButton

        anchors.left: x3dButton.right;
        anchors.leftMargin: UM.Theme.getSize("default_margin").width;
        anchors.top: importTypeLabel.bottom;
        style: UM.Theme.styles.tool_button;
        property bool needBorder: true
        checkable: true

        // The path to the icon.
        iconSource: "images/ply_icon.svg";
        
        // The text when holding the mouse over the icon.
        text: catalog.i18nc("@action:button", ".ply")
        // Otherwise the text when holding the mouse over the icon would hide under the other icons.
        z: 1

        // Sets the current import type to 'ply' and unchecks every other box.
        onClicked: setImportType(plyImportType)
    }

    // Checkbox for live reload.
    CheckBox
    {
        id: liveReloadCheckbox
        anchors.left: parent.left;
        anchors.top: stlButton.bottom;
        anchors.topMargin: UM.Theme.getSize("default_margin").width;
        style: UM.Theme.styles.checkbox;

        // The text for this checkbox.
        text: catalog.i18nc("@action:checkbox","Live Reload");

        // Calls getLiveReload and loads the entry state for live reload attribute.
        checked: UM.ActiveTool.properties.getValue("LiveReload");

        // Calls setLiveReload and sets the new state for live reload attribute.
        onClicked: UM.ActiveTool.setProperty("LiveReload", checked);
    }

    // Checkbox for auto arrange on reload.
    CheckBox
    {
        id: autoArrangeOnReloadCheckbox
        anchors.left: parent.left;
        anchors.top: liveReloadCheckbox.bottom;
        anchors.topMargin: UM.Theme.getSize("default_margin").width;
        style: UM.Theme.styles.checkbox;

        // The text for this checkbox.
        text: catalog.i18nc("@action:checkbox","Auto Arrange on reload");

        // Calls getAutoArrangeOnReload and loads the entry state for auto arrange on reload attribute.
        checked: UM.ActiveTool.properties.getValue("AutoArrangeOnReload");

        // Calls setAutoArrangeOnReload and sets the new state for auto arrange on reload attribute.
        onClicked: UM.ActiveTool.setProperty("AutoArrangeOnReload", checked);
    }

    // Checkbox for auto scale on read.
    CheckBox
    {
        id: autoScaleOnReadCheckbox
        anchors.left: parent.left;
        anchors.top: autoArrangeOnReloadCheckbox.bottom;
        anchors.topMargin: UM.Theme.getSize("default_margin").width;
        style: UM.Theme.styles.checkbox;

        // The text for this checkbox.
        text: catalog.i18nc("@action:checkbox","Auto Scale on read");

        // Calls getAutoScaleOnRead and loads the entry state for auto scale on read attribute.
        checked: UM.ActiveTool.properties.getValue("AutoScaleOnRead");

        // Calls setAutoScaleOnRead and sets the new state for auto scale on read attribute.
        onClicked: UM.ActiveTool.setProperty("AutoScaleOnRead", checked);
    }

    // Checkbox for show scale message.
    CheckBox
    {
        id: showScaleMessageCheckbox
        anchors.left: parent.left;
        anchors.top: autoScaleOnReadCheckbox.bottom;
        anchors.topMargin: UM.Theme.getSize("default_margin").width;
        style: UM.Theme.styles.checkbox;

        // The text for this checkbox.
        text: catalog.i18nc("@action:checkbox","Show Scale Message");

        // Calls getShowScaleMessage and loads the entry state for show scale message attribute.
        checked: UM.ActiveTool.properties.getValue("ShowScaleMessage");

        // Calls setShowScaleMessage and sets the new state for show scale message attribute.
        onClicked: UM.ActiveTool.setProperty("ShowScaleMessage", checked);
    }
}
