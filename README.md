# BarracudaQt

## Installation

### Python Installation 
Download Miniconda for Python 3.7 if not already installed. https://docs.conda.io/en/latest/miniconda.html

Open the Anaconda Prompt. Create the barracuda environment by downloading the the barracuda-env text file. Change directories to where you placed the text file create the barracuda python environment. 

~~~
cd \path\to\env\txtfile\

conda create --name CEpy37 --file barracuda-env.txt
conda activate CEpy37
python -m pip install opencv_python nidaqmx pycromanager
conda deactivate
~~~

### BarracudaQt Download & PyCharm Setup

Download the BarracudaQt repository and extract the files to the folder you want. Alternatively you can use git clone the repository to a folder. 

~~~
git clone https://github.com/aPeter1/BarracudaQt.git
~~~

If you are using PyCharm (Python IDE) you can open the BarracudaQt project folder. Set the project interpreter to CEpy37 (File>>Settings>>Project: BarracudaQt>>Project Interpreter). Click the settings button and select "Add" to add a new conda environment. Select Existing Environment and select the path location of the interpreter to be the python inside the conda env (for example: C:\Users\UserName\Miniconda3\envs\CEpy37\pyton.exe). Select 'OK' to keep the settings. 


### Micromanager Installation (if using Micromangaer to control hardware and/or get images)

Install the latest version of Micro-Manager 2 (https://micro-manager.org/wiki/Version_2.0)

Open Mincro-Manager 2, and under Tools>>Options select the box titled "Run on Server 4762".

Before you open the controller for pycromanager, make sure Micro-Manager 2 is running. 

### Thorlabs Kinesis

Download Thorlabs Kinesis from their website and restart the computer. Load the software and check the labjack can be accessed by kinesis. If the labjack is new you will need to make sure the correct Serial number is recorded in the Thorlabs Labjack Class. 

### Digilent Waveforms
Download Digilent Waveforms from the digilent inc. website. Install waveforms to your computer and verify you can access the Analog Discovery or desired device from the waveforms software. 

### Hardware Functionality

Create a new CESystems class or use a pre-defined class. Make sure that every function in the class works ( or at least the functions you require).
When your CESystems class is working, change the CESystems subclass object under CEControl. Alternatively you can make your own program using the CESystems.
For testing new functionality you may find it is easier to run CESystems from a Console, or Jupyter Notebook then when the
changes have been finalized move to adding it to the GUI. 
