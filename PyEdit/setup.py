import os
from setuptools import setup, find_packages


def set_dir():
    d = ''.join(__file__.split('/')[:-1])
    if d == '':
        return
    os.chdir('/'.join(__file__.split('/')[:-1]))


set_dir()

dat_files = ['Data/ui.ui', 'Data/pyedit.png',
             'Data/theme.xml', 'Data/custom_theme.css']
setup(
    name='PyEdit',
    version='1.3.0',
    description='A Python Editor using GTK',
    long_description=str(open('README.rst').read()),
    author='AstralDev',
    author_email='ekureedem480@gmail.com',
    license='LGPL',
    keywords='editor development',
    classifiers=["Development Status :: 4 - Beta",
                 "Environment :: X11 Applications :: GTK",
                 "Intended Audience :: Developers"
    ],
    python_requires='>=3',
    install_requires=['autopep8', 'jedi', 'markdown', "PyGObject"],
    packages=find_packages(include=['pyedit', 'pyedit.PyEditxN']),
    data_files=[('share/PyEdit/Data/', dat_files), 
                ('share/PyEdit/Data/128x128/', ['Data/128x128/pyedit.png']),
                ('share/PyEdit/Data/256x256/', ['Data/256x256/pyedit.png']),
                ('bin', ['Data/pyedit']), ('/.pyedit', []),
                ('share/applications', ['PyEdit.desktop']),
                ('share/icons/hicolor/512x512/apps',['Data/pyedit.png']),
                ('share/icons/hicolor/128x128/apps', ['Data/128x128/pyedit.png']),
                ('share/icons/hicolor/64x64/apps', ['Data/64x64/pyedit.png']),
                ('share/icons/hicolor/256x256/apps', ['Data/256x256/pyedit.png'])
                ]
)
