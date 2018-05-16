.. _intro-hello:

===================
Hello, World! Guide
===================

Overview
========
**Estimated time to complete:**
    30 to 60 minutes

In this guide, you will:
    - develop a simple Hello, World! app and tests in one of several languages 
    - define simple test and production environments using `Dockerfiles <https://docs.docker.com/engine/reference/builder/>`_
    - configure floop with the app
    - create Docker environments on one or more target devices
    - push source code from your host device to target devices
    - build code on target devices
    - test code on target devices in a test operating system environment on the target
    - run code on target devices in a production operating system environment on the target

In the end, each target device should greet you with "Hello, World!"

If you have Linux-based target devices, you can use them for this guide. Otherwise, follow along to see how to use Docker Machines on your host to run and test floop using just your computer.

Prerequisites
==============
At least one of the following:
    - One or more ARM devices running a Linux-based operating system with `kernel version 3.10+ <https://docs.docker.com/engine/faq/#how-far-do-docker-containers-scale>`_. For example, `Orange Pi Zero <http://www.orangepi.org/orangepizero/>`_ running `Armbian <https://www.armbian.com/orange-pi-zero/>`_ mainline kernel.
        If you use target hardware, please make sure the operating system on each device follows the :ref:`intro-os`. 
    - One or more Docker Machines running on your host. To see how to do this, check the `Docker Machine Tutorial <https://docs.docker.com/machine/get-started/>`_ for how to run local Docker Machines using Virtualbox. Once you install any necessary dependencies, you can typically start a new machine as follows: 
        .. code-block:: bash

          #!/bin/bash
          docker-machine create \
          --driver virtualbox \
          --virtualbox-memory 1024 \
          floop0

        That creates a new Docker Machine called *floop0* with 1GB of virtual memory.

        When you are finished, you can clean up as follows:
        ::
          #!/bin/bash
          docker-machine rm -f floop0

        If you want to test floop with multiple local devices, you can use the procedure above to make new devices and name them whatever you want, removing them when you are finished.
      

1. Install Floop
================
Check out the :ref:`intro-install` here.

2. Develop a Simple App
=======================
To start, we will make a simple app to print "Hello, World!" to the console. We will also add a small test suite to make sure our code works.

.. tabs::

    .. tab:: C++ 

        Make a new project folder with a src folder inside:
        ::
            mkdir -p ./project/src && cd ./project
       
        We need a function to print "Hello, World!" in order to test it
        outside of the main routine.
        
        Add the following code to a file called **hello.cpp**:

        .. literalinclude:: ../../../src/cpp/hello.cpp
            :language: c++

        We need a header file in order to share the *hello* function 
        between the main routine and the test routine.

        Add the following code to a file called **hello.h**:
            
        .. literalinclude:: ../../../src/cpp/hello.h
            :language: c++

        We need a test routine in order to test the *hello* function.
        We will use the Google Test library to run our tests.

        Add the following code to a file called **hello_test.cpp**:

        .. literalinclude:: ../../../src/cpp/hello_test.cpp
            :language: c++

        Finally, we need a main routine to run the *hello* function
        in production.

        Add the following code to a file called **main.cpp**:

        .. literalinclude:: ../../../src/cpp/main.cpp
            :language: c++


    .. tab:: Python

        Make a new project folder with a src folder inside:
        ::
            mkdir -p ./project/src && cd ./project

        We need a function to print "Hello, World". This function
        will double as our main routine if the file containing
        the *hello* function is called as a Python script.

        Add the following code to a file called **hello.py**:

        .. literalinclude:: ../../../src/python/hello.py
            :language: python

        We need a test suite to test our *hello* function.
        We will use the pytest library to run our tests. 

        Add the following code to a file called **hello_test.py**:

        .. literalinclude:: ../../../src/python/hello_test.py
            :language: python

        In order for Python to consider our **src** folder as a package so that we can import code from **hello.py** into **hello_test.py**, add a blank file called **__init__.py**:
        ::
            touch ./src/__init__.py

        Test our code on the host:
        ::
            python ./src/hello.py

        You should see "Hello, World!" on the console.

We now have a simple app. In order to test and to run this app, we need to define test and run environments.

3. Define Test and Production Environments
==========================================
We need to define a test and a runtime environment so we can run our tests to make sure that the code will work during deployment. For this purpose, floop uses Docker to create runtime environments with all dependencies and code installed as needed.  

Both the test and production environments will run inside a virtual operating system on your target devices. This standardizes your test and production environments across devices, despite different underlying hardware and operating systems installed on that hardware.

Since testing often requires different dependencies and run behavior than a production environment, we need one build file for each environment. 

.. tabs::

    .. tab:: C++ 

        First, define the test environment.
        
        We will start with a Debian Jessie operating system image, install a C++ compiler, install a testing library (Google Test), and set the default behavior of the environment to run the tests. 

        To accomplish these steps, add the following code to a file called **Dockerfile.test**:

        .. literalinclude:: ../../../src/cpp/Dockerfile.test
           
        At the end of the **Dockerfile.test** environment, it calls a script called **test.sh**. This script should compile all the code that needs to be tested then run that code inside of the test environment.

        Add the following code to a file called **test.sh**:

        .. literalinclude:: ../../../src/cpp/test.sh

        Now when we run our floop tests, we will automatically re-compile all new code alongside our testing utilities, then run the tests.

        Next, define the run environment.

        As with the test environment, we will start with a Debian Jessie operating system image and install a C++ compiler. Unlike the test environment, we no longer need to install the testing library. We will also need to set the default behavior of the environment to run the code.

        To accomplish these steps, add the following code to a file called **Dockerfile**:

        .. literalinclude:: ../../../src/cpp/Dockerfile

        At the end of the **Dockerfile** environment, it calls a script called **run.sh**. This script should compile all the code that needs to be run then run that code inside of the run environment.

        Add the following code to a file called **run.sh**:

        .. literalinclude:: ../../../src/cpp/run.sh

Configure the App with Floop
============================
floop reads all project configuration from a single JSON configuration file. This configuration defines the details of source code, device network addresses, and initial authentication details.

We will use floop In order to generate a default configuration template and then modify that template to match our device and network configuration.

From within the **project** folder, run:
::
    floop config

This will generate a default configuration called **floop.json**.

This configuration is based on the following default values (this is a Python dictionary that gets written to JSON):

.. literalinclude:: ../../../floop/config.py
    :lines: 10-21

The calls to the *which* function automatically set the path of docker-machine and rsync as they are installed on your system. If needed, you can edit **floop.json** to set the paths to each binary dependency. This may be useful if you need to use a different version of docker-machine or rsync than the default version for your system.

floop looks for source code on your host computer at *host_source_directory*. You can change the value to point to the relative path of your source code from the **floop.json** file. For the purposes of this guide, the default **./src** should work if you run floop from the **project** directory.

When you run floop, it will automatically copy code from *host_source_directory* to *device_target_directory*. You
