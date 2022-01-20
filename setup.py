import setuptools
from EggplantLibrary.version import VERSION

long_description = """
The Eggplant Library for [Robot Framework](https://robotframework.org/) allows calling
[eggPlant Functional](https://www.eggplantsoftware.com/eggplant-functional-downloads) scripts via XML RPC
using [eggDrive](http://docs.testplant.com/ePF/using/epf-about-eggdrive.htm).  
It considers **eggPlant scripts as low level keywords** and exposes them for usage in **high level keywords and test cases in Robot Framework**.  
So the scripts themselves have to be created in eggPlant, not in Robot Framework.        

The eggPlant itself should be launched in eggDrive mode from outside.

See the [Eggplant Library homepage](https://github.com/amochin/robotframework-eggplant) for more information.
"""

setuptools.setup(
    name="robotframework-eggplantlibrary",
    version=VERSION,    
    author="Andrei Mochinin",    
    description="Robot Framework eggPlant Library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/amochin/robotframework-eggplant",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: Microsoft :: Windows",
    ],
    install_requires=[
        'robotframework',
        'Pillow',
    ],
    python_requires='>=3.9',
)