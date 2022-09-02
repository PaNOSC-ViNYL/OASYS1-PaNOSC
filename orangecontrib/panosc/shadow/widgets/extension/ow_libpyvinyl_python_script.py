import os, sys

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtWidgets import QApplication, QFileDialog

from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui

from orangecontrib.esrf.shadow.util.python_script import PythonConsole

from orangecontrib.shadow.util.shadow_objects import ShadowBeam
from orangecontrib.shadow.util.shadow_util import ShadowCongruence, ShadowPlot
from oasys.widgets import widget
from PyQt5.QtCore import QRect

import inspect
import numpy
import Shadow




class ShadowLibpyvinylPythonScript(widget.OWWidget):

    name = "Shadow pylibvinyl Python Script"
    description = "Shadow pylibvinyl Python Script"
    icon = "icons/python_script.png"
    maintainer = "Manuel Sanchez del Rio"
    maintainer_email = "srio(@at@)esrf.eu"
    priority = 50
    category = "Tools"
    keywords = ["script"]

    inputs = [("Input Beam", ShadowBeam, "setBeam")]

    input_shadow_data=None


    script_file_flag = Setting(0)
    script_file_name = Setting("tmp.py")


    #
    #
    #
    IMAGE_WIDTH = 890
    IMAGE_HEIGHT = 680

    # want_main_area=1

    is_automatic_run = Setting(True)

    error_id = 0
    warning_id = 0
    info_id = 0

    MAX_WIDTH = 1320
    MAX_HEIGHT = 700

    CONTROL_AREA_WIDTH = 405
    TABS_AREA_HEIGHT = 560


    def __init__(self, show_automatic_box=True, show_general_option_box=True):
        super().__init__() # show_automatic_box=show_automatic_box)


        geom = QApplication.desktop().availableGeometry()
        self.setGeometry(QRect(round(geom.width()*0.05),
                               round(geom.height()*0.05),
                               round(min(geom.width()*0.98, self.MAX_WIDTH)),
                               round(min(geom.height()*0.95, self.MAX_HEIGHT))))

        self.setMaximumHeight(self.geometry().height())
        self.setMaximumWidth(self.geometry().width())

        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)

        self.general_options_box = gui.widgetBox(self.controlArea, "General Options", addSpace=True, orientation="horizontal")
        self.general_options_box.setVisible(show_general_option_box)

        if show_automatic_box :
            gui.checkBox(self.general_options_box, self, 'is_automatic_run', 'Automatic Execution')


        #
        #
        #
        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Refresh Script", callback=self.refresh_script)
        font = QFont(button.font())
        font.setBold(True)
        button.setFont(font)
        palette = QPalette(button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Blue'))
        button.setPalette(palette) # assign new palette
        button.setFixedHeight(45)


        gui.separator(self.controlArea)

        gen_box = oasysgui.widgetBox(self.controlArea, "Script Generation", addSpace=False, orientation="vertical", height=530, width=self.CONTROL_AREA_WIDTH-5)

        gui.comboBox(gen_box, self, "script_file_flag", label="write file with script",
                     items=["No", "Yes"], labelWidth=300,
                     sendSelectedValue=False, orientation="horizontal")

        box1 = gui.widgetBox(gen_box, orientation="horizontal")
        oasysgui.lineEdit(box1, self, "script_file_name", "Script File Name", labelWidth=150, valueType=str,
                          orientation="horizontal")
        self.show_at("self.script_file_flag == 1", box1)




        tabs_setting = oasysgui.tabWidget(self.mainArea)
        tabs_setting.setFixedHeight(self.IMAGE_HEIGHT)
        tabs_setting.setFixedWidth(self.IMAGE_WIDTH)

        tab_scr = oasysgui.createTabPage(tabs_setting, "Python Script")
        tab_out = oasysgui.createTabPage(tabs_setting, "System Output")

        self.pythonScript = oasysgui.textArea(readOnly=False)
        self.pythonScript.setStyleSheet("background-color: white; font-family: Courier, monospace;")
        self.pythonScript.setMaximumHeight(self.IMAGE_HEIGHT - 250)

        script_box = oasysgui.widgetBox(tab_scr, "", addSpace=False, orientation="vertical", height=self.IMAGE_HEIGHT - 10, width=self.IMAGE_WIDTH - 10)
        script_box.layout().addWidget(self.pythonScript)

        console_box = oasysgui.widgetBox(script_box, "", addSpace=True, orientation="vertical",
                                          height=150, width=self.IMAGE_WIDTH - 10)

        self.console = PythonConsole(self.__dict__, self)
        console_box.layout().addWidget(self.console)

        self.shadow_output = oasysgui.textArea()

        out_box = oasysgui.widgetBox(tab_out, "System Output", addSpace=True, orientation="horizontal", height=self.IMAGE_WIDTH - 45)
        out_box.layout().addWidget(self.shadow_output)

        #############################

        button_box = oasysgui.widgetBox(tab_scr, "", addSpace=True, orientation="horizontal")

        gui.button(button_box, self, "Run Script", callback=self.execute_script, height=40)
        # gui.button(button_box, self, "Save Script to File", callback=self.save_script, height=40)

        gui.rubber(self.controlArea)

        self.process_showers()

    def callResetSettings(self):
        pass

    def execute_script(self):

        self._script = str(self.pythonScript.toPlainText())
        self.console.write("\nRunning script:\n")
        self.console.push("exec(_script)")
        self.console.new_prompt(sys.ps1)


    def save_script(self):
        # file_name = QFileDialog.getSaveFileName(self, "Save File to Disk", os.getcwd(), filter='*.py')[0]
        file_name = self.script_file_name
        if not file_name is None:
            if not file_name.strip() == "":
                file = open(file_name, "w")
                file.write(str(self.pythonScript.toPlainText()))
                file.close()


    def setBeam(self, beam):
        if ShadowCongruence.checkEmptyBeam(beam):
            if ShadowCongruence.checkGoodBeam(beam):
                # sys.stdout = EmittingStream(textWritten=self.writeStdOut)

                self.input_beam = beam

                if self.is_automatic_run:
                    self.refresh_script()

            else:
                QtWidgets.QMessageBox.critical(self, "Error",
                                           "Data not displayable: No good rays or bad content",
                                           QtWidgets.QMessageBox.Ok)

    def refresh_script(self):
        optical_element_list_start = []
        optical_element_list_end = []

        self.pythonScript.setText("")

        for history_element in self.input_beam.getOEHistory():
            if not history_element._shadow_source_start is None:
                optical_element_list_start.append(history_element._shadow_source_start.src)
            elif not history_element._shadow_oe_start is None:
                optical_element_list_start.append(history_element._shadow_oe_start._oe)

            if not history_element._shadow_source_end is None:
                optical_element_list_end.append(history_element._shadow_source_end.src)
            elif not history_element._shadow_oe_end is None:
                optical_element_list_end.append(history_element._shadow_oe_end._oe)


        try:
            if self.script_file_flag == 0:
                script_file = ""
            else:
                script_file = self.script_file_name
            self.pythonScript.setText(make_python_script_from_list(optical_element_list_start,
                                                                   script_file=script_file,
                                                                   ) )
        except:
            self.pythonScript.setText(
                "Problem in writing python script:\n" + str(sys.exc_info()[0]) + ": " + str(sys.exc_info()[1]))

        if self.script_file_flag:
            self.save_script()



#
# automatic creation of python scripts
#

def make_python_script_from_list(list_optical_elements1, script_file="",):
    """
    program to build automatically a python script to run shadow3

    the system is read from a list of instances of Shadow.Source and Shadow.OE

    :argument list of optical_elements A python list with intances of Shadow.Source and Shadow.OE objects
    :param script_file: a string with the name of the output file (default="", no output file)
    :return: template with the script
    """

    # make sure that the list does not contain lists

    haslist = sum([isinstance(i, list) for i in list_optical_elements1])

    list_optical_elements = list_optical_elements1
    if haslist:
        while (haslist > 0):
            newlist = []
            for i in list_optical_elements:
                if isinstance(i, list):
                    newlist.extend(i)
                else:
                    newlist.append(i)
            list_optical_elements = newlist
            haslist = sum([isinstance(i, list) for i in list_optical_elements])

    # make sure that the list does not contain compoundOE (developed)

    hascomp = sum(
        [isinstance(i, (Shadow.CompoundOE, Shadow.ShadowLibExtensions.CompoundOE)) for i in list_optical_elements])

    if hascomp:
        newlist = []
        for i in list_optical_elements:
            if isinstance(i, (Shadow.CompoundOE, Shadow.ShadowLibExtensions.CompoundOE)):
                newlist.extend(i.list)
            else:
                newlist.append(i)
        list_optical_elements = newlist

    template_import = """#
# Python script to run shadow3 using libpyvinyl.
#
import numpy
from libpyvinyl.Parameters.Collections import CalculatorParameters
from libpyvinyl.Parameters.Parameter import Parameter
from shadow3libpyvinyl.Shadow3Calculator import Shadow3Calculator
from shadow3libpyvinyl.Shadow3Data import Shadow3BeamFormat, Shadow3OpenPMDFormat


"""

    n_elements = len(list_optical_elements)
    #
    # source
    #


    template_define_source = """
def add_source(parameters):
    #
    # Define variables. See https://raw.githubusercontent.com/oasys-kit/shadow3/master/docs/source.nml
    #
"""

    isource = -1
    for i, element in enumerate(list_optical_elements):
        if isinstance(element, Shadow.Source):
            isource = i

    if isource == -1:
        raise Exception("Source not found")

    ioe = isource
    oe1B = list_optical_elements[isource]
    template_define_source += "\n"
    if isinstance(oe1B, Shadow.Source):
        oe1 = Shadow.Source()


    memB = inspect.getmembers(oe1B)
    mem = inspect.getmembers(oe1)

    for i, var in enumerate(memB):
        ivar = mem[i]
        ivarB = memB[i]
        if ivar[0].isupper():
            if isinstance(ivar[1], numpy.ndarray):

                if not ((ivar[1] == ivarB[1]).all()):
                    line = "    p = Parameter('oe" + str(ioe) + "." + ivar[0] + "',''); p.value = numpy.array(" + str(ivarB[1].tolist()) + ") ; parameters.add(p)\n"
                    template_define_source += line

            else:
                if ivar[1] != ivarB[1]:
                    if isinstance(ivar[1], (str)):
                        line = "    p = Parameter('oe" + str(ioe) + "." + ivar[0] + "',''); p.value = " + str(ivarB[1]).strip() + " ; parameters.add(p)\n"
                        if "SPECIFIED" in line:
                            pass
                        else:
                            template_define_source += line
                    elif isinstance(ivar[1], (bytes)):
                        line = "    p = Parameter('oe" + str(ioe) + "." + ivar[0] + "',''); p.value = '" + ivarB[1].strip().decode("utf-8") + "' ; parameters.add(p)\n"
                        if "SPECIFIED" in line:
                            pass
                        else:
                            template_define_source += line
                    else:
                        line = "    p = Parameter('oe" + str(ioe) + "." + ivar[0] + "',''); p.value = " + str(ivarB[1]) + " ; parameters.add(p)\n"
                        template_define_source += line

    template_define_source += """
    return parameters
    """


    #
    # trace
    #

    template_define_beamline = """

def add_beamline(parameters):

    """

    template_define_beamline += """
    #
    # Define variables. See https://raw.githubusercontent.com/oasys-kit/shadow3/master/docs/oe.nml
    #
"""

    for ioe, oe1B in enumerate(list_optical_elements):
        template_define_beamline += "\n"
        if isinstance(oe1B, Shadow.Source):
            oe1 = Shadow.Source()
        elif isinstance(element, Shadow.OE):
            oe1 = Shadow.OE()
        elif isinstance(element, Shadow.IdealLensOE):
            oe1 = Shadow.IdealLensOE()

        if ioe != 0:

            if isinstance(oe1B, Shadow.IdealLensOE):
                template_define_beamline += "   p = Parameter('oe" + str(ioe) + ".T_SOURCE', '') ; p.value = " + str(oe1B.T_SOURCE).strip() + " ; parameters.add(p)\n"
                template_define_beamline += "   p = Parameter('oe" + str(ioe) + ".T_IMAGE' , '') ; p.value = " + str(oe1B.T_IMAGE).strip() +  " ; parameters.add(p)\n"
                template_define_beamline += "   p = Parameter('oe" + str(ioe) + ".focal_x' , '') ; p.value = " + str(oe1B.focal_x).strip() +  " ; parameters.add(p)\n"
                template_define_beamline += "   p = Parameter('oe" + str(ioe) + ".focal_z' , '') ; p.value = " + str(oe1B.focal_z).strip() +  " ; parameters.add(p)\n"
            else:
                memB = inspect.getmembers(oe1B)
                mem = inspect.getmembers(oe1)
                for i, var in enumerate(memB):
                    ivar = mem[i]
                    ivarB = memB[i]
                    if ivar[0].isupper():
                        if isinstance(ivar[1], numpy.ndarray):

                            if not ((ivar[1] == ivarB[1]).all()):
                                line = "    p = Parameter('oe" + str(ioe) + "." + ivar[0] + "','') ; p.value = numpy.array(" + str(
                                    ivarB[1].tolist()) + ") ; parameters.add(p)\n"
                                template_define_beamline += line

                        else:
                            if ivar[1] != ivarB[1]:
                                if isinstance(ivar[1], (str)):
                                    line = "    p = Parameter('oe" + str(ioe) + "." + ivar[0] + "','') ; p.value = " + str(ivarB[1]).strip() + " ; parameters.add(p)\n"

                                    if "SPECIFIED" in line:
                                        pass
                                    else:
                                        template_define_beamline += line
                                elif isinstance(ivar[1], (bytes)):
                                    line = "    p = Parameter('oe" + str(ioe) + "." + ivar[0] + "','') ; p.value = '" + ivarB[1].strip().decode("utf-8") + "' ; parameters.add(p)\n"

                                    if "SPECIFIED" in line:
                                        pass
                                    else:
                                        template_define_beamline += line
                                else:
                                    line = "    p = Parameter('oe" + str(ioe) + "." + ivar[0] + "','') ; p.value = " + str(ivarB[1]) + " ; parameters.add(p)\n"
                                    template_define_beamline += line



    template_define_beamline += """\n

    return parameters

    """

    #
    # put together all pieces
    #
    template = ""
    template += template_import

    template += template_define_source


    if n_elements > 1:
        template += template_define_beamline


    #
    # run
    #

    template += """
#
# main
#

parameters = CalculatorParameters()
"""

    # template += "calculator.setParams(number_of_optical_elements=%d)\n" % (n_elements - 1)
    template += "parameters = add_source(parameters)"


    if n_elements > 1:
        template += """
parameters = add_beamline(parameters)
"""

    template += """
calculator  = Shadow3Calculator("", None, parameters=parameters)
calculator.backengine()


#
# output files 
#
calculator.parameters.to_json("my_parameters.json")
# print(calculator.parameters)

# calculator.data.write("tmp.dat", Shadow3BeamFormat)    # raw data format
calculator.data.write("tmp.h5", Shadow3OpenPMDFormat)  # openPMD data format

    
    
#
# plots
#
import Shadow
beam = Shadow.Beam(N=calculator.data.get_data()["nrays"])
beam.rays = calculator.data.get_data()["rays"]
Shadow.ShadowTools.plotxy(beam, 1, 3, nbins=101, nolost=1, title="Real space")

"""


    if script_file != "":
        open(script_file, "wt").write(template)
        print("File written to disk: %s" % (script_file))

    return template



if __name__ == "__main__":
    import sys
    import Shadow

    class MyBeam():
        def getOEHistory(selfself):
            return []
        # pass
    beam_to_analize = Shadow.Beam()
    beam_to_analize.load("/users/srio/Oasys/star.01")
    my_beam = MyBeam()
    my_beam._beam = beam_to_analize

    a = QApplication(sys.argv)
    ow = ShadowLibpyvinylPythonScript()
    ow.show()
    ow.input_beam = my_beam
    a.exec_()
    ow.saveSettings()