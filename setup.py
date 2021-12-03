from setuptools import setup

setup(
    name = 'zeva12can',
    version = '0.1',
    description =  "Utilties for communicating with Zeva BMS-12 over CAN bus.",
    packages = ["zeva12can"],
    install_requires = ['python-can'],
    entry_points = {
        "console_scripts": [
            "monitor=zeva12can.monitor:cli"]
    }
)
