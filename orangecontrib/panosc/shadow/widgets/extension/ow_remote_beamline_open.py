import os, numpy

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QDialog, QInputDialog, QListWidget
from orangewidget import gui,widget
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui, congruence
from oasys.widgets import widget as oasyswidget

import json
import urllib.request

from orangecanvas.application.canvasmain import CanvasMainWindow
from orangecanvas.preview import previewdialog, previewmodel

# import six

class RemoteBeamlineLoader(oasyswidget.OWWidget):
    name = "Remote Repository Beamline Loader"
    description = "Utility: Remote Repository Beamline Loader"
    icon = "icons/remote_beamline_open.png"
    maintainer = "Aljosa Hafner"
    maintainer_email = "aljosa.hafner(@at@)ceric-eric.eu"
    priority = 2
    category = "Utility"
    keywords = ["remote", "repository", "load", "read", "beamline"]

    want_main_area = 0

    beam_file_name = Setting("")
    selectedIndex = Setting([0])
    selectedURL = Setting("")
    repository = Setting("https://raw.githubusercontent.com/PaNOSC-ViNYL/Oasys-PaNOSC-Workspaces/master/mainList.json")

    def __init__(self):
        super().__init__()

        """Browse recent schemes. Return QDialog.Rejected if the user
        canceled the operation and QDialog.Accepted otherwise.

        """

        ## https://raw.githubusercontent.com/PaNOSC-ViNYL/Oasys-PaNOSC-Workspaces/master/mainList.json
        # https://github.com/PaNOSC-ViNYL/Oasys-PaNOSC-Workspaces
        #
        # self.setFixedWidth(590)
        # self.setFixedHeight(300)

        wWidth = 650
        wHeight = 400

        main_box = oasysgui.widgetBox(self.controlArea, "", orientation="vertical", width=wWidth-20, height=wHeight-20)

        self.le_repoName = oasysgui.lineEdit(main_box, self, "repository", "Repository JSON URL: ", labelWidth=150,
                                             valueType=str, orientation="vertical", callbackOnType=self.changeRepoURL)

        upper_box = oasysgui.widgetBox(main_box, "", orientation="horizontal", width=wWidth-20, height=wHeight-80)

        left_box = oasysgui.widgetBox(upper_box, "List of workspaces", orientation="vertical",
                                        width=wWidth/2.-13., height=wHeight-120)

        self.beamlineList = gui.listBox(left_box, self, "selectedIndex", callback=self.selectedItemListBox)

        right_box = oasysgui.widgetBox(upper_box, "Metadata", addSpace=True,
                                        orientation="vertical",
                                        width=wWidth/2.-12., height=wHeight-120)

        self.metadataLabel = ""
        self.md_label = "%(metadataLabel)s"
        self.box_metaData = gui.label(right_box, self, self.md_label, orientation="vertical")

        gui.separator(main_box, height=10)

        button = gui.button(main_box, self, "Select and open...", callback=self.open_selected_scheme)
        button.setFixedHeight(38)

        gui.rubber(self.controlArea)

        self.changeRepoURL()

    def changeRepoURL(self):

        response = urllib.request.urlopen(self.repository)
        beamlineJson = json.loads(response.read())

        beamlines = beamlineJson['OASYS_Remote_Workspaces_PaNOSC']['beamlines']
        namesOfBeamlines = []
        self.metadataList = []
        self.urlsOfBeamlines = []


        for i, beamline in enumerate(beamlines):
            currentName = beamline['institute'] + ' - ' + beamline['name']
            currentURL = beamline['url_workspace']
            currentMetadata = "Institute: " + beamline['institute'] + "\n" + "Beamline: " + beamline['name'] + "\n" + "Creator: " + beamline['uploaded_by'] + "\n" + "Date: " + beamline['date'] + "\n" + "Other info: " + beamline['url_info']
            namesOfBeamlines.append(currentName)
            self.metadataList.append(currentMetadata)
            self.urlsOfBeamlines.append(currentURL)
            self.beamlineList.insertItem(i, currentName)

    # Code for opening remote OWS (from welcome dialogue)

    def selectedItemListBox(self):
        self.selectedURL = self.urlsOfBeamlines[self.selectedIndex[0]]
        self.metadataLabel = self.metadataList[self.selectedIndex[0]]

    def open_selected_scheme(self):
        """Open a new scheme. Return QDialog.Rejected if the user canceled
        the operation and QDialog.Accepted otherwise.

        """
        # document = self.current_document()
        # if document.isModifiedStrict():
        #     if self.ask_save_changes() == QDialog.Rejected:
        #         return QDialog.Rejected
        #
        # dlg = QInputDialog(self)
        # dlg.setInputMode(QInputDialog.TextInput)
        # dlg.setWindowTitle(self.tr("Open Remote Orange Workflow File"))
        # dlg.setLabelText("URL:")
        # dlg.setTextValue(self.tr("http://"))
        # dlg.resize(500, 50)
        # ok = dlg.exec_()
        # url = dlg.textValue()
        #

        return CanvasMainWindow.load_scheme(CanvasMainWindow, filename=str(self.selectedURL))


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    a = QApplication(sys.argv)
    ow = RemoteBeamlineLoader()
    # ow.le_beam_file_name.setText("/users/srio/Oasys/tmp.h5")
    # ow.workspace_units_to_cm = 100
    ow.show()
    a.exec_()
    ow.saveSettings()
    # beam = loadShadowOpenPMD(filename="/users/srio/Oasys/tmp.h5")
