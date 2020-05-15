// Import the standard GUI elements from QTQuick
import QtQuick 2.2
import QtQuick.Controls 1.1

// Import the Uranium GUI elements, which are themed for Cura
import UM 1.1 as UM

// Dialog from Uranium
UM.Dialog
{
    // Everything needs an id to be adressed elsewhere in the file
    id: base

    // We don't want the dialog to block input in the main window
    modality: Qt.NonModal

    // Setting the dimensions of the dialog window and prohibiting resizing
    width: 520
    height: 550
    minimumWidth: 520
    minimumHeight: 550

    // Connecting our variable to the computed property of our manager
    property string historyText: manager.historyText

    // Flickables make the contained elements scrollable
    Flickable {

      id: scroll_area

      width: 500
      height: 500

      // Position the flickable relative to the dialog with some margins
      anchors.top: base.bottom
      anchors.topMargin: 10
      anchors.left: base.left
      anchors.leftMargin: 10

      // We set the content height to the height of the contained text element
      contentHeight: history_text.height

      // We only want vertical scrolling
      flickableDirection: Flickable.VerticalFlick

      // Don't show the content of this Flickable outside of its bounds
      clip: true

      // Always scroll the contained element to the top if something is added
      contentY: history_text.height - scroll_area.height

      // Text element, which only renders text. Has no input functionality
      Text
      {
          id: history_text

          // We don't set the height, so the element can grow with its content
          width: 500

          // Allow the text to be styled with Markdown commands
          textFormat: Text.StyledText

          // Contained text wraps anywhere - even inside of words
          wrapMode: Text.WrapAnywhere

          // The contained text is read from the prepared variable
          text: historyText
      }
    }

    // Text element, which allows input
    TextField
    {
        id: code_input

        width: 500

        anchors.top: scroll_area.bottom
        anchors.topMargin: 10
        anchors.left: base.left
        anchors.leftMargin: 10

        text: ""

        // When we press return an event is fired and the appropriate method on
        // our manager is called with the previously entered line of code as the
        // parameter. Then we accept the event - otherwise it would be bubbled
        // up the chain of GUI elements, which we don't want because the dialog
        // closes if it gets a return pressed event.
        Keys.onReturnPressed:
        {
            manager.executeSourceLine(code_input.text)
            event.accepted = true
        }
    }
}
