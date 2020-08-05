import os

try:
    from setuptools import find_packages, setup
except AttributeError:
    from setuptools import find_packages, setup

NAME = 'OASYS1-PaNOSC'
VERSION = '0.0.4'
ISRELEASED = True

DESCRIPTION = 'OASYS extension for PaNOSC'
README_FILE = os.path.join(os.path.dirname(__file__), 'README.md')
LONG_DESCRIPTION = open(README_FILE).read()
AUTHOR = 'Manuel Sanchez del Rio, Aljosa Hafner'
AUTHOR_EMAIL = 'srio@esrf.eu,  aljosa.hafner@ceric-eric.eu'
URL = 'https://github.com/PaNOSC-ViNYL/OASYS1-PaNOSC'
DOWNLOAD_URL = 'https://github.com/PaNOSC-ViNYL/OASYS1-PaNOSC'
LICENSE = 'GPLv3'

KEYWORDS = (
    'PaNOSC',
    'WP5',
    'simulations',
    'oasys1',
)

CLASSIFIERS = (
    'Development Status :: 4 - Beta',
    'Environment :: X11 Applications :: Qt',
    'Environment :: Console',
    'Environment :: Plugins',
    'Programming Language :: Python :: 3',
    'Intended Audience :: Science/Research',
)

SETUP_REQUIRES = (
    'setuptools',
)

INSTALL_REQUIRES = (
    'setuptools',
    'openpmd-api',
)

PACKAGES = find_packages(exclude=('*.tests', '*.tests.*', 'tests.*', 'tests'))

PACKAGE_DATA = {
    "orangecontrib.panosc.shadow.widgets.extension":["icons/*.png", "icons/*.jpg", "miscellanea/*.txt"],
}

NAMESPACE_PACAKGES = ["orangecontrib",
                      "orangecontrib.panosc",
                      "orangecontrib.panosc.shadow",
                      "orangecontrib.panosc.shadow.widgets",
                      ]

ENTRY_POINTS = {
    'oasys.addons' : (
                      "Shadow PaNOSC = orangecontrib.panosc.shadow",
                      ),
    'oasys.widgets' : (
        "Shadow PaNOSC Extension = orangecontrib.panosc.shadow.widgets.extension",
    ),
    'oasys.menus' : ("panoscoasysmenu = orangecontrib.panosc.menu",)
}

if __name__ == '__main__':
    try:
        import PyMca5, PyQt4

        raise NotImplementedError("This version of PaNOSC Oasys Extensions doesn't work with Oasys1 beta.\nPlease install OASYS1 final release: http://www.elettra.eu/oasys.html")
    except:
        setup(
              name = NAME,
              version = VERSION,
              description = DESCRIPTION,
              long_description = LONG_DESCRIPTION,
              author = AUTHOR,
              author_email = AUTHOR_EMAIL,
              url = URL,
              download_url = DOWNLOAD_URL,
              license = LICENSE,
              keywords = KEYWORDS,
              classifiers = CLASSIFIERS,
              packages = PACKAGES,
              package_data = PACKAGE_DATA,
              #          py_modules = PY_MODULES,
              setup_requires = SETUP_REQUIRES,
              install_requires = INSTALL_REQUIRES,
              #extras_require = EXTRAS_REQUIRE,
              #dependency_links = DEPENDENCY_LINKS,
              entry_points = ENTRY_POINTS,
              namespace_packages=NAMESPACE_PACAKGES,
              include_package_data = True,
              zip_safe = False,
              )
