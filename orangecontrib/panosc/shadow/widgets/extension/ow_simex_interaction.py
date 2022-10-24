import os

from PyQt5 import QtWidgets
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QPalette, QColor, QFont


from orangecontrib.shadow.util.shadow_objects import ShadowBeam
from orangecontrib.panosc.shadow.util.openPMD import saveShadowToHDF

from orangewidget import gui,widget
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui, congruence
from oasys.widgets import widget as oasyswidget

from orangecontrib.shadow.util.shadow_util import ShadowCongruence

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from matplotlib import cm
import json

import warnings

# import six

class CalculateWithSimEx(oasyswidget.OWWidget):
    name = "Run SimEx Calculation"
    description = "Utility: Seamless interaction with SimEx calculators"
    icon = "icons/simex_interactor.png"
    maintainer = "Aljosa Hafner"
    maintainer_email = "aljosa.hafner(@at@)ceric-eric.eu"
    priority = 10
    category = "Utility"
    keywords = ["simex", "sample", "simulation", "interaction", "seamless", "panosc"]

    want_main_area = 0
    beam_file_name = Setting("")
    input_file = Setting("params.json")
    gapd_sample_file = Setting("single-cu.xyz")
    gapd_output_file = Setting("diffr_poly_1.txt")
    select_input = 0
    select_calculator = 0

    is_automatic_run= Setting(1)

    send_footprint_beam = QSettings().value("output/send-footprint", 0, int) == 1

    if send_footprint_beam:
        inputs = [("Input Beam", object, "setBeam")]
    else:
        inputs = [("Input Beam", ShadowBeam, "setBeam")]

    outputs = [{"name": "Beam",
                "type": ShadowBeam,
                "doc": "Shadow Beam",
                "id": "beam"}, ]

    input_beam = None

    def __init__(self):
        super().__init__()

        try:
            from SimEx.Calculators.GAPDPhotonDiffractor import GAPDPhotonDiffractor
            self.is_installed = True

        except:
            self.is_installed = False
            QMessageBox.information(self, "Warning", "GAPD is NOT installed!", QMessageBox.Ok)

        self.runaction = widget.OWAction("Write Shadow File", self)
        self.runaction.triggered.connect(self.write_file)
        self.addAction(self.runaction)

        # self.setFixedWidth(590)
        # self.setFixedHeight(190)

        gui.checkBox(self.controlArea, self, 'is_automatic_run', 'Automatic Execution')

        is_installed_label = gui.label(self.controlArea, self, "GAPD is NOT installed!")
        font = QFont(is_installed_label.font())
        font.setBold(True)
        is_installed_label.setFont(font)
        is_installed_label.setStyleSheet('color: red')
        # palette = QPalette(is_installed_label.palette())
        # palette.setColor(QPalette.Text, QColor('red'))
        # palette.setColor(QPalette.Base, QColor(243, 240, 140))
        # is_installed_label.setPalette(palette)

        if self.is_installed:
            is_installed_label.setText("GAPD is installed")
            font = QFont(is_installed_label.font())
            font.setBold(True)
            is_installed_label.setFont(font)
            is_installed_label.setStyleSheet('color: green')
            # palette = QPalette(is_installed_label.palette())
            # palette.setColor(QPalette.Text, QColor('green'))
            # palette.setColor(QPalette.Base, QColor(243, 240, 140))
            # is_installed_label.setPalette(palette)

        left_box_1 = oasysgui.widgetBox(self.controlArea, "Shadow Beam Input", addSpace=True, orientation="vertical", width=620, height=130)

        gui.comboBox(left_box_1, self, "select_input", label="Select Input",
                     items=["From Workspace", "From File"], labelWidth=240,
                     callback=self.set_SelectInput, sendSelectedValue=False, orientation="horizontal")


        self.use_SelectInput_OWS_empty = oasysgui.widgetBox(left_box_1, "", addSpace=False, addToLayout=False, width=0)
        self.use_SelectInput_OWS = oasysgui.widgetBox(left_box_1, "", addSpace=False, orientation="vertical", width=600, height=65)
        
        self.use_SelectInput_OWS_box = oasysgui.widgetBox(self.use_SelectInput_OWS, "", addSpace=False, orientation="horizontal", width=600)
        self.le_beam_file_name = oasysgui.lineEdit(self.use_SelectInput_OWS_box, self, "beam_file_name", "File Name", labelWidth=120, valueType=str, orientation="horizontal")
        gui.button(self.use_SelectInput_OWS_box, self, "...", callback=self.selectFile)
        
        gui.button(self.use_SelectInput_OWS, self, "Write openPMD/hdf File", callback=self.write_file)

        self.use_SelectInput_File_empty = oasysgui.widgetBox(left_box_1, "", addSpace=False, addToLayout=False, width=0)
        self.use_SelectInput_File = oasysgui.widgetBox(left_box_1, "", addSpace=False, orientation="horizontal", width=600, height=65)
        self.le_beam_file_name = oasysgui.lineEdit(self.use_SelectInput_File, self, "beam_file_name", "Shadow File Name", labelWidth=120, valueType=str, orientation="horizontal")
        gui.button(self.use_SelectInput_File, self, "...", callback=self.selectFile)

        self.set_SelectInput()
        # button.setFixedHeight(35)

        left_box_2 = oasysgui.widgetBox(self.controlArea, "SimEx Calculator Parameters", addSpace=True, orientation="vertical", width=620)

        gui.comboBox(left_box_2, self, "select_calculator", label="Select Calculator",
                     items=["GAPD", "Another calculator"], labelWidth=240,
                     callback=self.set_SelectCalculator, sendSelectedValue=False, orientation="horizontal")

        self.use_SelectCalculator_GAPD_empty = oasysgui.widgetBox(left_box_2, "", addSpace=False, addToLayout=False, width=0)
        self.use_SelectCalculator_GAPD = oasysgui.widgetBox(left_box_2, "", addSpace=False, orientation="vertical", width=600)

        self.le_input_box = oasysgui.widgetBox(self.use_SelectCalculator_GAPD, "", addSpace=False, orientation="horizontal", width=600)
        self.le_input = oasysgui.lineEdit(self.le_input_box, self, "input_file", "Input JSON File", labelWidth=120, valueType=str, orientation="horizontal")
        gui.button(self.le_input_box, self, "...", callback=self.selectFileInput)

        self.le_gapd_sample_box = oasysgui.widgetBox(self.use_SelectCalculator_GAPD, "", addSpace=False, orientation="horizontal", width=600)
        self.le_gapd_sample = oasysgui.lineEdit(self.le_gapd_sample_box, self, "gapd_sample_file", "Sample File [xyz]", labelWidth=120, valueType=str, orientation="horizontal")
        gui.button(self.le_gapd_sample_box, self, "...", callback=self.selectFileGAPDSample)

        self.le_gapd_output_box = oasysgui.widgetBox(self.use_SelectCalculator_GAPD, "", addSpace=False, orientation="horizontal", width=600)
        self.le_gapd_output = oasysgui.lineEdit(self.le_gapd_output_box, self, "gapd_output_file", "Output File", labelWidth=120, valueType=str, orientation="horizontal")
        gui.button(self.le_gapd_output_box, self, "...", callback=self.selectFileGAPDOutput)

        self.set_SelectCalculator()
        
        self.button_box_GAPD = oasysgui.widgetBox(self.use_SelectCalculator_GAPD, "", addSpace=False, orientation="horizontal", width=600)
        button2 = gui.button(self.button_box_GAPD, self, "Calculate", callback=self.calculateSimEx)
        button3 = gui.button(self.button_box_GAPD, self, "Plot Output File", callback=self.plotSimEx)

        gui.rubber(self.controlArea)

    def set_SelectInput(self):
        self.use_SelectInput_File.setVisible(self.select_input == 1)
        self.use_SelectInput_OWS.setVisible(self.select_input == 0)
        self.use_SelectInput_File_empty.setVisible(self.select_input == 0)
        self.use_SelectInput_OWS_empty.setVisible(self.select_input == 1)

    def set_SelectCalculator(self):
        self.use_SelectCalculator_GAPD.setVisible(self.select_calculator == 0)
        self.use_SelectCalculator_GAPD_empty.setVisible(self.select_calculator == 1)

    def selectFile(self):
        self.le_beam_file_name.setText(oasysgui.selectFileFromDialog(self, self.beam_file_name, "Open Shadow File"))

    def selectFileInput(self):
        self.le_input.setText(oasysgui.selectFileFromDialog(self, self.input_file, "Select Input File"))
    def selectFileGAPDSample(self):
        self.le_gapd_sample.setText(oasysgui.selectFileFromDialog(self, self.gapd_sample_file, "Select GAPD Sample File"))
    def selectFileGAPDOutput(self):
        self.le_gapd_output.setText(oasysgui.selectFileFromDialog(self, self.gapd_output_file, "Select GAPD Output File"))

    def setBeam(self, beam):
        send_footprint_beam = QSettings().value("output/send-footprint", 0, int) == 1

        if send_footprint_beam and isinstance(beam, list):
            self.input_beam = beam[1]
        elif ShadowCongruence.checkEmptyBeam(beam) and ShadowCongruence.checkGoodBeam(beam):
            self.input_beam = beam
        else:
            QtWidgets.QMessageBox.critical(self, "Error", "No good rays or bad content", QtWidgets.QMessageBox.Ok)
            return

        if self.is_automatic_run: self.write_file_temp()

    def write_file(self):
        self.setStatusMessage("")
        print(">>>>> called write_file ")
        try:
            if ShadowCongruence.checkEmptyBeam(self.input_beam):
                if ShadowCongruence.checkGoodBeam(self.input_beam):
                    if congruence.checkFileName(self.beam_file_name):
                        # self.input_beam.writeToFile(self.beam_file_name)
                        saveShadowToHDF(self.input_beam._beam, filename=self.beam_file_name)
                        print(">>>>> File %s written to disk" % self.beam_file_name)

                        path, file_name = os.path.split(self.beam_file_name)

                        self.setStatusMessage("File Out: " + file_name)

                        self.send("Beam", self.input_beam)
                else:
                    QtWidgets.QMessageBox.critical(self, "Error", "No good rays or bad content", QtWidgets.QMessageBox.Ok)
        except Exception as exception:
            QtWidgets.QMessageBox.critical(self, "Error", str(exception), QtWidgets.QMessageBox.Ok)

    def write_file_temp(self):
        self.setStatusMessage("")
        print(">>>>> called write_file_temp ")
        try:
            if ShadowCongruence.checkEmptyBeam(self.input_beam):
                if ShadowCongruence.checkGoodBeam(self.input_beam):
                    saveShadowToHDF(self.input_beam._beam, filename="temp.h5")
                    print(">>>>> File %s written to disk" % "temp.h5")

                    self.setStatusMessage("Temp file saved")
                    
                    self.send("Beam", self.input_beam)
                else:
                    QtWidgets.QMessageBox.critical(self, "Error", "No good rays or bad content", QtWidgets.QMessageBox.Ok)
        except Exception as exception:
            QtWidgets.QMessageBox.critical(self, "Error", str(exception), QtWidgets.QMessageBox.Ok)
    
    def plotSimEx(self):
        try:
            outfile = self.gapd_output_file

            plt.figure('Spectrum')
            spec = np.loadtxt('/home/aljosa/Oasys/development_sprint/py/spectrum.txt')
            plt.plot(spec[:, 0], spec[:, 1])
    
            data = np.loadtxt(outfile, ndmin=2)
            print(data.shape)
            fig = plt.figure('Linear', figsize=(10, 5))
            plt.imshow(data,
                    vmax=0.5,
                    cmap=cm.jet)
            plt.colorbar()
        
            data = np.loadtxt(outfile, ndmin=2)
            print(data.shape)
            fig = plt.figure('Logarithmic', figsize=(10, 5), )
            plt.imshow(data,
                    cmap=cm.jet,
                    norm=colors.LogNorm(vmin=data.min(), vmax=data.max())
                    )
            plt.colorbar()
            plt.show()
        except Exception as exception:
            QtWidgets.QMessageBox.critical(self, "Error: Cannot Read File", str(exception), QtWidgets.QMessageBox.Ok)

    def importJson(self, filePath):
        with open(filePath, 'r') as j:
            jsonAsDict = json.loads(j.read())
        return jsonAsDict

    def calculateSimEx(self):

        try:
            from SimEx.Calculators.GAPDPhotonDiffractor import GAPDPhotonDiffractor
            from SimEx.Parameters.GAPDPhotonDiffractorParameters import GAPDPhotonDiffractorParameters
            from SimEx.Parameters.DetectorGeometry import DetectorGeometry, DetectorPanel
            from SimEx.Utilities.Units import meter, electronvolt, joule, radian
            QMessageBox.information(self, "Import Successful", "GAPD was successfully imported!", QMessageBox.Ok)

            self.setStatusMessage("Reading JSON file")

            paramsDict = self.importJson(self.input_file)

            self.setStatusMessage("Parameters loaded")

            detector_panel = DetectorPanel(
                ranges={
                    'fast_scan_min': paramsDict['Detector']['fast_scan_min'],
                    'fast_scan_max': paramsDict['Detector']['fast_scan_max'],
                    'slow_scan_min': paramsDict['Detector']['slow_scan_min'],
                    'slow_scan_max': paramsDict['Detector']['slow_scan_max']
                },
                pixel_size=paramsDict['Detector']['pixel_size [um]'] * 1e-6 * meter,
                photon_response=1.0,
                distance_from_interaction_plane=paramsDict['Detector']['Sample to detector distance [mm]'] * 1e-3 * meter,
                corners={
                    'x': paramsDict['Detector']['corner_x'],
                    'y': paramsDict['Detector']['corner_y']
                },
            )
            detector_geometry = DetectorGeometry(panels=[detector_panel])

            # Polychromatic beam setup

            self.setStatusMessage("Setting input beam")

            if self.select_input == 1:
                beam = self.beam_file_name
            else:
                self.write_file_temp()
                beam = "temp.h5"

            # Diffractor setup
            outfile = self.gapd_output_file
            if os.path.exists(outfile) == False:
                open(outfile, "w").close

            self.setStatusMessage("Setting Parameters")
            parameters = GAPDPhotonDiffractorParameters(detector_geometry=detector_geometry, beam_parameters=beam,
                                                        number_of_spectrum_bins=100)

            self.setStatusMessage("Calculating")
            diffractor = GAPDPhotonDiffractor(parameters=parameters,
                                              input_path=self.gapd_sample_file,
                                              output_path=outfile)

            diffractor.backengine()

            self.setStatusMessage("Done!")

            # Plot
            self.plotSimEx()
            # plt.figure('Spectrum')
            # spec = np.loadtxt('/home/aljosa/Oasys/development_sprint/py/spectrum.txt')
            # plt.plot(spec[:, 0], spec[:, 1])

            # data = np.loadtxt(outfile, ndmin=2)
            # print(data.shape)
            # fig = plt.figure('Linear', figsize=(10, 5))
            # plt.imshow(data,
            # vmax=0.5,
            # cmap=cm.jet)
            # plt.colorbar()

            # data = np.loadtxt(outfile, ndmin=2)
            # print(data.shape)
            # fig = plt.figure('Logarithmic', figsize=(10, 5), )
            # plt.imshow(data,
            # cmap=cm.jet,
            # norm=colors.LogNorm(vmin=data.min(), vmax=data.max())
            # )
            # plt.colorbar()
            # plt.show()

            return None

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e), QMessageBox.Ok)
            self.setStatusMessage("GAPD NOT installed!")

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    a = QApplication(sys.argv)
    ow = CalculateWithSimEx()
    ow.show()
    a.exec_()
    ow.saveSettings()
