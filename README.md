# BarracudaQt

## Installation

### Python Installation 
Download Miniconda for Python 3.7 if not already installed. https://docs.conda.io/en/latest/miniconda.html

Open the Anaconda Prompt. Create the barracuda environment by downloading the the barracuda-env text file. Change directories to where you placed the text file create the barracuda python environment. 

~~~
cd \path\to\env\txtfile\

conda create --name CEpy37 --file \path\to\env\txtfile\barracuda-env.txt
conda activate CEpy37
python -m pip install opencv_python nidaqmx onnx onnx_tf
conda deactivate
~~~

### BarracudaQt Download & PyCharm Setup

Download the BarracudaQt repository and extract the files to the folder you want. Alternatively you can use git clone the repository to a folder. 

~~~
git clone https://github.com/aPeter1/BarracudaQt.git
~~~

If you are using PyCharm (Python IDE) you can open the BarracudaQt project folder. Set the project interpreter to CEpy37 (File>>Settings>>Project: BarracudaQt>>Project Interpreter). Click the settings button and select "Add" to add a new conda environment. Select Existing Environment and select the path location of the interpreter to be the python inside the conda env (for example: C:\Users\UserName\Miniconda3\envs\CEpy37\pyton.exe). Select 'OK' to keep the settings. 


### Micromanager Installation (if using Micromangaer to control hardware and/or get images)

Download micromanager from https://micro-manager.org/

In the Anaconda prompt create a separate python environment to control micromanger. At the time the CE instrument was created micromanager did not have python 3 support. In order to use micromanager we create a separate subprocess in python 2 and transfer data and commands back and port over using the multiprocessing module. 

Create the separate python environment for micromanager. 

~~~
conda create --name CEpy27 python=2.7
~~~

Under the config folder. Place the configuration file for your stage, camera, or whatever hardware object you wish to use Micro-Manager for. Config files for Nikon Eclipse Ti, QCam3, and CoolSnap (PVCam) are already present. 

Under Hardware>>MicroControlClient.py change the PYTHON2_PATH variable to the python 2 executable for the CEpy27 environment.
For example a common location will be: "C:\Users\UserName\Miniconda3\envs\CEPy27\python"

### Hardware Checklist 

You will need to check each piece of hardware is working individually before running the program. Under Testing there is a hardware-test file that will test each core component of the hardware folder. If that can run with no failures you are good to run the CE System. 
