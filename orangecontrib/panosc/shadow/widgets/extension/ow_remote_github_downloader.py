from PyQt5.QtWidgets import QApplication
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtCore import QRect

from orangewidget import gui,widget
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui, congruence
from oasys.widgets import widget as oasyswidget

import urllib.request
from urllib.request import urlretrieve

import re

def get_usual_servers():
    urls = [
        "",
        "https://github.com/oasys-kit/ShadowOui-tutorial",
        "https://github.com/oasys-kit/ShadowOui-Tutorial/tree/master/OTHER_EXAMPLES",
        "https://github.com/oasys-kit/ShadowOui-Tutorial/tree/master/SOS-WORKSHOP/EBS-WIGGLERS",
        "https://github.com/oasys-kit/oasys_school/tree/master/second/session_xoppy",
        "https://github.com/oasys-kit/oasys_school/tree/master/second/session_shadowoui",
        "https://github.com/oasys-kit/oasys_school/tree/master/second/session_srw",
        "https://github.com/oasys-esrf-kit/oasys_hercules/tree/main/2022",
        "https://github.com/oasys-esrf-kit/OasysWorkspaces",
        "https://github.com/PaNOSC-ViNYL/Oasys-PaNOSC-Workspaces",
        "https://github.com/oasys-esrf-kit/paper-multioptics-resources/tree/main/workspaces",
        "https://github.com/oasys-als-kit/Paper_JSR_yi5097/tree/master/Oasys",
        "https://github.com/oasys-als-kit/Paper_JSR_hf5419",
        "https://github.com/srio/paper-hierarchical-resources/tree/master/Oasys",
    ]
    names = [
        "",
        "ShadowOui-tutorial",
        "ShadowOui-tutorial more",
        "ShadowOui-tutorial ESRF wigglers",
        "Oasys school: xoppy",
        "Oasys school: shadowOui",
        "Oasys school: SRW",
        "Oasys HERCULES school",
        "ESRF Oasys repo",
        "PaNOSC Oasys repo",
        "Paper multioptics",
        "Paper heat load compensation",
        "Paper diaboloid",
        "Paper hierarchical",
    ]
    return names, urls

def ls_ows(target_url = "https://github.com/PaNOSC-ViNYL/Oasys-PaNOSC-Workspaces"):
    data = urllib.request.urlopen(target_url)
    list_files = []
    for line in data:
        line1 = str(line)

        if ".ows" in line1:
            try:
                found = re.search('ows">(.+?)</a>', line1).group(1)
                list_files.append(found)
            except:
                pass

    return list_files

def get_raw_dir(target_url):

    if "tree" in target_url:
        # https://github.com/oasys-kit/ShadowOui-Tutorial/tree/master/OTHER_EXAMPLES
        # https://raw.githubusercontent.com/oasys-kit/ShadowOui-Tutorial/master/OTHER_EXAMPLES/CRL_Snigirev_1996.ows
        return "https://raw.githubusercontent.com/" + target_url[19:].replace("tree/","") + "/"
    else:
        # https://raw.githubusercontent.com/PaNOSC-ViNYL/Oasys-PaNOSC-Workspaces/master/EBS_ID18.ows
        # "https://raw.githubusercontent.com/PaNOSC-ViNYL/Oasys-PaNOSC-Workspaces/master/EBS_ID32.ows"
        return "https://raw.githubusercontent.com/"+target_url[19:]+"/master/"

def get_ows_data(url, debug=0):
    url_raw = get_raw_dir(url)
    list_files = ls_ows(url)
    titles = []
    descriptions = []
    url_files1 = []
    for file in list_files:
        url_file = url_raw + file
        url_files1.append(url_file)
        if debug: print(">>", url_file)
        try:
            data = urllib.request.urlopen(url_file).read(2000).decode('utf-8')
        except:
            raise ("Error reading data from ", url_file)

        try:
            description = re.search('<scheme description="(.+?)" title', data).group(1)
            descriptions.append(description)
        except:
            descriptions.append("")

        try:
            title = re.search('title="(.+?)"', data).group(1)
            titles.append(title)
        except:
            titles. append("")


    return list_files, url_files1, titles, descriptions

class RemoteGithubDownloader(oasyswidget.OWWidget):
    name = "Remote Github Repository Downloader"
    description = "Utility: Remote Github Repository Downloader"
    icon = "icons/github.png"
    maintainer = "Aljosa Hafner and Manuel Sanchez del Rio"
    maintainer_email = "srio(@at@)esrf.eu"
    priority = 13
    category = "Utility"
    keywords = ["remote", "repository", "load", "read", "beamline"]

    want_main_area = 0
    beam_file_name = Setting("")
    selectedIndex = Setting([0])
    selectedURL = Setting("")
    selectedFile = Setting("")
    servers_list = Setting(0)
    # repository = Setting("https://github.com/oasys-kit/ShadowOui-tutorial")
    repository = Setting("https://github.com/PaNOSC-ViNYL/Oasys-PaNOSC-Workspaces")
    urlselectedfile = Setting("")

    beamlines = []    # workspace names
    descriptions = [] # as stored in the workspace
    url_files = []    # the raw url to open remote



    def __init__(self):
        super().__init__()

        """Browse recent schemes. Return QDialog.Rejected if the user
        canceled the operation and QDialog.Accepted otherwise.

        """


        wWidth = 650
        wHeight = 400


        geom = QApplication.desktop().availableGeometry()
        self.setGeometry(QRect(round(geom.width()*0.05),
                               round(geom.height()*0.05),
                               round(min(geom.width()*0.98, wWidth)),
                               round(min(geom.height()*0.95, wHeight))))

        self.setMaximumHeight(self.geometry().height())
        self.setMaximumWidth(self.geometry().width())

        main_box = oasysgui.widgetBox(self.controlArea, "", orientation="vertical", width=wWidth-40, height=wHeight-30)

        gui.comboBox(main_box, self, "servers_list", label="Select a server",
                     items=get_usual_servers()[0], labelWidth=300,
                     sendSelectedValue=False, orientation="horizontal", callback=self.set_server)

        box1 = gui.widgetBox(main_box, orientation="horizontal")
        self.le_repoName = oasysgui.lineEdit(box1, self, "repository", "Repository URL: ", labelWidth=120,
                                             valueType=str, orientation="horizontal", callback=self.change_repo_url,
                                             )

        box2 = gui.widgetBox(main_box, orientation="horizontal")
        upper_box = oasysgui.widgetBox(box2, "", orientation="horizontal", width=wWidth-50, height=wHeight-40)

        left_box = oasysgui.widgetBox(upper_box, "List of workspaces", orientation="vertical",
                                        width=wWidth//2-13, height=wHeight-143)

        self.beamlineList = gui.listBox(left_box, self, "selectedIndex", callback=self.select_beamline)

        right_box = oasysgui.widgetBox(upper_box, "Description", addSpace=True,
                                        orientation="vertical",)
                                        # width=wWidth/2.-12., height=wHeight-143)

        self.metadataLabel = ""
        self.md_label = "%(metadataLabel)s"
        self.box_metaData = gui.label(right_box, self, self.md_label, orientation="vertical")

        box3 = gui.widgetBox(main_box, orientation="vertical")
        box33 = gui.widgetBox(box3, orientation="horizontal")
        oasysgui.lineEdit(box33, self, "urlselectedfile", "Selected file URL: ", labelWidth=120,
                                             valueType=str, orientation="horizontal",
                                             )

        box34 = gui.widgetBox(box3, orientation="horizontal")
        button = gui.button(box34, self, "Download...", callback=self.download_scheme)
        button.setFixedHeight(35)

        # button = gui.button(box34, self, "Open...", callback=self.open_scheme)
        # button.setFixedHeight(35)

        gui.rubber(self.controlArea)

        self.change_repo_url()

    def change_repo_url(self):

        self.clear_repo_url()

        try:
            beamlines, url_files, titles, descriptions = get_ows_data(self.repository)
        except:
            QMessageBox.information(self, "Error", "Error retrieving files from " + self.repository, QMessageBox.Ok)
            return

        self.descriptions = descriptions
        self.url_files = url_files
        self.beamlines = beamlines

        for i, beamline in enumerate(beamlines):
            currentName = beamline
            self.beamlineList.insertItem(i, currentName)

    def clear_repo_url(self):
        self.beamlineList.clear()
        self.selectedIndex = [0]
        self.urlselectedfile = ""


    def select_beamline(self):
        if len(self.selectedIndex) > 0:
            self.metadataLabel   = self.descriptions[self.selectedIndex[0]]
            self.selectedFile = self.beamlines[self.selectedIndex[0]]
            self.urlselectedfile = self.url_files[self.selectedIndex[0]]
        else:
            self.metadataLabel   = ""
            self.selectedFile    = ""
            self.urlselectedfile = ""



    def download_scheme(self):
        if self.selectedFile == "":
            QMessageBox.information(self, "Error", "Please select a file", QMessageBox.Ok)
            return

        filedialog = QtWidgets.QFileDialog(self)
        filename, _ = filedialog.getSaveFileName(self, "Save workspace", self.selectedFile, "Oasys files (*.ows)")

        if filename == "":
            return

        try:
            filepath, http_msg = urlretrieve(self.selectedURL,
                                             filename=filename,
                                             reporthook=None,
                                             data=None)
            print("Workspace file %s downloaded to %s" % (self.selectedURL, filepath))
            QMessageBox.information(self, "Success", "File saved: " + filepath, QMessageBox.Ok)

        except IOError:
            QMessageBox.information(self, "Error", "Error writing file: " + filename, QMessageBox.Ok)

    def set_server(self):
        names, urls = get_usual_servers()

        self.repository = urls[self.servers_list]
        self.change_repo_url()



if __name__ == "__main__":

    if False:
        names, servers = get_usual_servers()
        print("names:", names)
        print("servers:", servers)
        for server in servers:
            print("")
            print(">>>>>>>>>>>>>>>>>server: ", server)
            if server != "":
                beamlines, url_files, titles, descriptions = get_ows_data(server)
                print("          beamlines: ", beamlines)
                print("          url_files: ", url_files)
                print("          titles: ", titles)
                print("          descriptions: ", descriptions)

    import sys
    a = QApplication(sys.argv)
    ow = RemoteGithubDownloader()
    ow.show()
    a.exec_()
    ow.saveSettings()


