# EasyPip

# How to repair Dependency problems in Python environment configuration files

This project contains the implementation of EasyPip to automatically detect and solve errors in configuration files of python projects.   

EasyPip formulates dependency solving into a graph-search problem. It can detect the dependency problems in Python environment configuration files and finds the optimal solutions by solving the feasible path with minimal modifcation.


# Prerequisites
* Python 3.6 or higher. We recommend to use Python V3.6.4.


# Run
To repair dependency problems in Python environment configuration files,  execute the main() of ./exp/main.py; The program will stop the running when it times out.
To reproduce the execution environment, run the following command:
* pip install -r requirements.txt
* cd /PATH/TO/EasyPip

# Config EasyPip
edit ./exp/alg/common.py 
* BASE_PATH = "YOUR EasyPip PATH"
* DEF_FILENAME = "YOUR Environmen Configuration FILE"

execute the main() of ./exp/main.py

The genrated results consists three parts:
	recommanded python version
	the direct dependency 
	the transitive dependency 

# EXAMPLE 
To try to run EasyPip, you can choose one of the file in the environment configuration files in ".\data\dependency_declaration_files". 
The output is corresponding recommanded configuration file, in which the first line is recommand Python version, and other lines are the direct and transitive depencies. 
If it cannot find a set of satisfied versions of this file, the root cause information is shown in the log file ".\EasyPip\exp\log" 

To check the correctness of a recommanded file, you can run the command "pip install -r dir_requirements.txt".

# We are happy to see any suggestion on EasyPip. If there is any question, please propose an issue without any hesitation. Thank you for your notice. 