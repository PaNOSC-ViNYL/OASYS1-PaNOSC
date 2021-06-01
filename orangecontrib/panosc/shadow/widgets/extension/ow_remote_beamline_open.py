import os, numpy

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QDialog, QInputDialog, QListWidget
from orangewidget import gui,widget
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui, congruence
from oasys.widgets import widget as oasyswidget

import json
import urllib.request

from orangecontrib.shadow.util.shadow_objects import ShadowBeam, ShadowOpticalElement, ShadowOEHistoryItem

from orangecontrib.panosc.shadow.util.openPMD import loadShadowOpenPMD
from orangecanvas.preview import previewdialog, previewmodel

import six

class RemoteBeamlineLoader(oasyswidget.OWWidget):
    name = "Remote Repository Beamline Loader"
    description = "Utility: Remote Repository Beamline Loader"
    icon = "icons/beam_file_reader.png"
    maintainer = "Aljosa Hafner"
    maintainer_email = "aljosa.hafner(@at@)ceric-eric.eu"
    priority = 2
    category = "Utility"
    keywords = ["remote", "repository", "load", "read", "beamline"]

    want_main_area = 0

    beam_file_name = Setting("")
    repository = Setting("https://raw.githubusercontent.com/PaNOSC-ViNYL/Oasys-PaNOSC-Workspaces/master/mainList.json")
    outputs = [{"name": "Beam",
                "type": ShadowBeam,
                "doc": "Shadow Beam",
                "id": "beam"}, ]

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

        main_box = oasysgui.widgetBox(self.controlArea, "", orientation="vertical", width=wWidth, height=wHeight)

        self.le_repoName = oasysgui.lineEdit(main_box, self, "repository", "Repository JSON: ", labelWidth=105, valueType=str, orientation="horizontal")

        upper_box = oasysgui.widgetBox(main_box, "", orientation="horizontal", width=wWidth-10, height=wHeight-75)

        left_box = oasysgui.widgetBox(upper_box, "List of workspaces", orientation="vertical",
                                        width=wWidth/2.-10., height=wHeight-80)

        self.beamlineList = gui.listBox(left_box, self)

        right_box = oasysgui.widgetBox(upper_box, "Metadata", addSpace=True,
                                        orientation="vertical",
                                        width=wWidth/2.-10., height=wHeight-80)

        self.box_metaData = oasysgui.widgetBox(right_box, "", orientation="vertical")

        gui.separator(main_box, height=5)

        button = gui.button(main_box, self, "Select")#, callback=self.read_file)
        button.setFixedHeight(40)

        gui.rubber(self.controlArea)
        urlJson = "https://raw.githubusercontent.com/PaNOSC-ViNYL/Oasys-PaNOSC-Workspaces/master/mainList.json"
        response = urllib.request.urlopen(urlJson)
        beamlineJson = json.loads(response.read())

        beamlines = beamlineJson['OASYS_Remote_Workspaces_PaNOSC']['beamlines']
        numberOfBeamlines = len(beamlines)
        namesOfBeamlines = []


        for i, beamline in enumerate(beamlines):
            currentName = beamline['institute'] + ' - ' + beamline['name']
            namesOfBeamlines.append(currentName)
            self.beamlineList.insertItem(i, currentName)

        # self.remote_schemes = []
        # items = [previewmodel.PreviewItem(name=title, path=path)
        #          for title, path in self.recent_schemes]
        # model = previewmodel.PreviewModel(items=items)
        #
        # dialog = previewdialog.PreviewDialog(self)
        # title = self.tr("Recent Workflows")
        # dialog.setWindowTitle(title)
        # template = ('<h3 style="font-size: 26px">\n'
        #             #'<img height="26" src="canvas_icons:Recent.svg">\n'
        #             '{0}\n'
        #             '</h3>')
        # dialog.setHeading(template.format(title))
        # dialog.setModel(model)
        #
        # model.delayedScanUpdate()
        #
        # status = dialog.exec_()
        #
        # index = dialog.currentIndex()
        #
        # dialog.deleteLater()
        # model.deleteLater()
        #
        # if status == QDialog.Accepted:
        #     doc = self.current_document()
        #     if doc.isModifiedStrict():
        #         if self.ask_save_changes() == QDialog.Rejected:
        #             return QDialog.Rejected
        #
        #     selected = model.item(index)
        #
        #     return self.load_scheme(six.text_type(selected.path()))

        # return status

        # left_box_1 = oasysgui.widgetBox(self.controlArea, "Shadow File Selection", addSpace=True, orientation="vertical",
        #                                  width=570, height=70)
        #
        # figure_box = oasysgui.widgetBox(left_box_1, "", addSpace=True, orientation="horizontal", width=550, height=35)
        #
        # self.le_beam_file_name = oasysgui.lineEdit(figure_box, self, "beam_file_name", "Shadow File Name",
        #                                             labelWidth=120, valueType=str, orientation="horizontal")
        # self.le_beam_file_name.setFixedWidth(330)
        #
        # gui.button(figure_box, self, "...", callback=self.selectFile)
        #
        # #gui.separator(left_box_1, height=20)
        #
        # button = gui.button(self.controlArea, self, "Read Shadow File", callback=self.read_file)
        # button.setFixedHeight(45)
        #
        # gui.rubber(self.controlArea)

    def selectFile(self):
        self.le_beam_file_name.setText(oasysgui.selectFileFromDialog(self, self.beam_file_name, "Open Shadow File"))

    def read_file(self):
        self.setStatusMessage("")

        try:
            if congruence.checkFileName(self.beam_file_name):
                beam = loadShadowOpenPMD(filename=self.beam_file_name)
                beam_out = ShadowBeam(beam=beam)

                beam_out.history.append(ShadowOEHistoryItem()) # fake Source
                beam_out._oe_number = 0

                # just to create a safe history for possible re-tracing
                beam_out.traceFromOE(beam_out, self.create_dummy_oe(), history=True)

                path, file_name = os.path.split(self.beam_file_name)

                self.setStatusMessage("Current: " + file_name)

                self.send("Beam", beam_out)
        except Exception as exception:
            QtWidgets.QMessageBox.critical(self, "Error",
                                       str(exception), QtWidgets.QMessageBox.Ok)


    def create_dummy_oe(self):
        empty_element = ShadowOpticalElement.create_empty_oe()

        empty_element._oe.DUMMY = self.workspace_units_to_cm

        empty_element._oe.T_SOURCE     = 0.0
        empty_element._oe.T_IMAGE = 0.0
        empty_element._oe.T_INCIDENCE  = 0.0
        empty_element._oe.T_REFLECTION = 180.0
        empty_element._oe.ALPHA        = 0.0

        empty_element._oe.FWRITE = 3
        empty_element._oe.F_ANGLE = 0

        return empty_element

    # Code for opening remote OWS (from welcome dialogue)

    def open_remote_scheme(self):
        """Open a new scheme. Return QDialog.Rejected if the user canceled
        the operation and QDialog.Accepted otherwise.

        """
        document = self.current_document()
        if document.isModifiedStrict():
            if self.ask_save_changes() == QDialog.Rejected:
                return QDialog.Rejected

        dlg = QInputDialog(self)
        dlg.setInputMode(QInputDialog.TextInput)
        dlg.setWindowTitle(self.tr("Open Remote Orange Workflow File"))
        dlg.setLabelText("URL:")
        dlg.setTextValue(self.tr("http://"))
        dlg.resize(500, 50)
        ok = dlg.exec_()
        url = dlg.textValue()

        if ok == 1 and url:
            return self.load_scheme(url)
        else:
            return QDialog.Rejected

    # Code for opening recent OWS (from welcome dialogue)

    def recent_scheme(self, *args):
        """Browse recent schemes. Return QDialog.Rejected if the user
        canceled the operation and QDialog.Accepted otherwise.

        """
        items = [previewmodel.PreviewItem(name=title, path=path)
                 for title, path in self.recent_schemes]
        model = previewmodel.PreviewModel(items=items)

        dialog = previewdialog.PreviewDialog(self)
        title = self.tr("Recent Workflows")
        dialog.setWindowTitle(title)
        template = ('<h3 style="font-size: 26px">\n'
                    #'<img height="26" src="canvas_icons:Recent.svg">\n'
                    '{0}\n'
                    '</h3>')
        dialog.setHeading(template.format(title))
        dialog.setModel(model)

        model.delayedScanUpdate()

        status = dialog.exec_()

        index = dialog.currentIndex()

        dialog.deleteLater()
        model.deleteLater()

        if status == QDialog.Accepted:
            doc = self.current_document()
            if doc.isModifiedStrict():
                if self.ask_save_changes() == QDialog.Rejected:
                    return QDialog.Rejected

            selected = model.item(index)

            return self.load_scheme(six.text_type(selected.path()))

        return status


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