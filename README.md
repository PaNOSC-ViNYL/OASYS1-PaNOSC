# OASYS1-PaNOSC
OASYS extensions for PaNOSC

This repository contains extensions to Oasys developed by PaNOSC. 

## Install as user

To install the add-on as user: 

+ In the Oasys window, open "Options->Add-ons..."
+ click the button "Add more" and enter "OASYS1-PaNOSC". You will see a
new entry "PaNOSCExtensions" in the add-on list. Check it and click "OK"
+ Restart Oasys.

![addon menu](https://github.com/oasys-PaNOSC-kit/OASYS1-PaNOSC-Extensions/blob/master/images/image2.png "addon menu")

Once it is installed, it should populate the widget bar on the side.

![side menu](https://github.com/oasys-PaNOSC-kit/OASYS1-PaNOSC-Extensions/blob/master/images/image1.png "side menu")

## Install as developper

To install it as developper, download it from github:
```
git clone  https://github.com/PaNOSC-ViNYL/OASYS1-PaNOSC
cd OASYS1-PaNOSC
```

Then link the source code to your Oasys python (note that you must use the python that Oasys uses):  
```
python -m pip install -e . --no-deps --no-binary :all:
```

When restarting Oasys, you will see the PaNOSC addons there.



