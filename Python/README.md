## Python Wrapper for NebulaSDK API

Python wrapper is an opensource project of Vzense Nebula API.

The goal of this project is to help developers use Vzense ToF camera via python method easily.

PythonSDK version: V1.0.8

### Supported Devices

- DS77Lite 
- DS77CLite
- DS77Pro  
- DS77CPro
- DS86
- DS87  
- DCAM650
- DCAM660

### Requirements

- python version : 3.7.x
- python modules : ctypes, numpy, opencv-python(display only)

### Directory

- **DS77**: the API and Sample code for DS77Lite/DS77Pro
- **DS77C**: the API and Sample code for DS77CLite/DS77CPro
- **DS86**: the API and Sample code for DS86 & DS87

### Quick Start

1. install modules:
```	 
pip install numpy
pip install opencv-python 
```
2. switch to Samples under the product directory, run the sample that you need. 
For example, go to the DS77/Samples/FrameViewer, then run 'python FrameViewer_DS77.py'

3. When using multiple network cards, set different IP network segments