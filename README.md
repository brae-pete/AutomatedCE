# BarracudaQt

## Installation

### Python Installation 
Download Miniconda for Python 3.7 if not already installed. https://docs.conda.io/en/latest/miniconda.html

Open the Anaconda Prompt. Create the barracuda environment by downloading the the barracuda-env text file. Change directories to where you placed the text file create the barracuda python environment. 

~~~
cd \path\to\env\txtfile\

conda create --name CEpy37 --file \path\to\env\txtfile\barracuda-env.txt
~~~


### Micromanager Installation (if using Micromangaer to control the software)

Download micromanager from https://micro-manager.org/

In the Anaconda prompt create a separate python environment to control micromanger. At the time the CE instrument was created micromanager did not have python 3 support. In order to use micromanager we create a separate subprocess in python 2 and transfer data and commands back and port over using the multiprocessing module. 

Create the separate python environment for micromanager. 

~~~
conda create --name CEpy27 python=2.7
~~~

### BarracudaQt Download

Download the BarracudaQt repository and extract the files to the folder you want. Alternatively you can use git clone the repository to a folder. 

~~~

~~~

