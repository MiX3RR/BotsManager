@echo off
echo Checking Python version...

python -c "import sys; version=sys.version_info; exit(0 if version.major==3 and version.minor>=10 else 1)" 2>NUL
if errorlevel 1 (
    echo Python 3.10 or higher is required!
    echo Current Python version:
    python --version
    echo Please install Python 3.10 or higher from python.org
    pause
    exit
)

echo Python version check passed!
echo Checking and installing required dependencies...

REM Standard library modules check
python -c "import os, subprocess, threading, time, tkinter, queue, logging, pathlib, sys, json, codecs" 2>NUL
if errorlevel 1 (
    echo Some standard library modules are missing. Please reinstall Python.
    pause
    exit
)

REM External dependencies check and install
python -c "import darkdetect" 2>NUL
if errorlevel 1 (
    echo Installing darkdetect...
    pip install darkdetect
) else (
    echo darkdetect is already installed
)

python -c "import pygetwindow" 2>NUL
if errorlevel 1 (
    echo Installing pygetwindow...
    pip install pygetwindow
) else (
    echo pygetwindow is already installed
)

echo All dependencies are installed successfully!
echo Starting BotsManager...

REM Use full path to Python and script
start "" "C:\Program Files\Python310\python.exe" "%~dp01v.py"
exit