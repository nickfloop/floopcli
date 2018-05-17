.. _intro-hello:

===================
Hello, World! Guide
===================

Overview
========
**Estimated time to complete:**
    30 to 60 minutes

In this guide, you will try out all of the floop commands. In order to do so, you will:
    - develop a simple Hello, World! app and tests in one of several languages 
    - define simple test and production environments using `Dockerfiles <https://docs.docker.com/engine/reference/builder/>`_
    - **configure** floop with the app
    - **create** floop target devices that handle communication with your real hardware targets
    - **push** source code from your host device to target devices
    - **build** code on target devices
    - **test** code on target devices in a test operating system environment on the target
    - **run** code on target devices in a production operating system environment on the target
    - **monitor** running or testing environments on target devices
    - **log** all events to the host 
    - **destroy** floop devices and reclaim resources on all target devices

In the end, each target device should greet you with "Hello, World!"

If you have Linux-based target devices, you can use them for this guide. Otherwise, follow along to see how to use Docker Machines on your host to run and test floop using just your computer.

Prerequisites
==============
At least one of the following:

.. tabs::

    .. tab:: ARM Devices 

        This is the option for using floop with real devices.

        You can use one or more ARM devices running a Linux-based operating system with `kernel version 3.10+ <https://docs.docker.com/engine/faq/#how-far-do-docker-containers-scale>`_. For example, `Orange Pi Zero <http://www.orangepi.org/orangepizero/>`_ running `Armbian <https://www.armbian.com/orange-pi-zero/>`_ mainline kernel.
            If you use target hardware, please make sure the operating system on each device follows the :ref:`intro-os`. 

    .. tab:: Docker Machines 

        This is the option for testing or evaluating floop before you use it with real devices.

        You can use one or more Docker Machines running on your host. To see how to do this, check the `Docker Machine Tutorial <https://docs.docker.com/machine/get-started/>`_ for how to run local Docker Machines using Virtualbox. Once you install Docker Machine and local machine dependencies, you can typically start a new machine as follows: 

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

        .. literalinclude:: ../../../example/src/cpp/hello.cpp
            :language: c++

        We need a header file in order to share the *hello* function 
        between the main routine and the test routine.

        Add the following code to a file called **hello.h**:
            
        .. literalinclude:: ../../../example/src/cpp/hello.h
            :language: c++

        We need a test routine in order to test the *hello* function.
        We will use the Google Test library to run our tests.

        Add the following code to a file called **hello_test.cpp**:

        .. literalinclude:: ../../../example/src/cpp/hello_test.cpp
            :language: c++

        Finally, we need a main routine to run the *hello* function
        in production.

        Add the following code to a file called **main.cpp**:

        .. literalinclude:: ../../../example/src/cpp/main.cpp
            :language: c++


    .. tab:: Python

        Make a new project folder with a src folder inside:
        ::
            mkdir -p ./project/src && cd ./project

        We need a function to print "Hello, World". This function
        will double as our main routine if the file containing
        the *hello* function is called as a Python script.

        Add the following code to a file called **hello.py**:

        .. literalinclude:: ../../../example/src/python/hello.py
            :language: python

        We need a test suite to test our *hello* function.
        We will use the pytest library to run our tests. 

        Add the following code to a file called **hello_test.py**:

        .. literalinclude:: ../../../example/src/python/hello_test.py
            :language: python

        In order for Python to consider our **src** folder as a package so that we can import code from **hello.py** into **hello_test.py**, add a blank file called **__init__.py**:
        ::
            touch ./src/__init__.py

        Test our code on the host:
        ::
            python ./src/hello.py

        You should see "Hello, World!" on the console.

We now have a simple app. In order to test and to run this app, we need to define test and run environments.

3. Define Test and Run Environments
==========================================
We need to define a test and a run environment so we can run our tests to make sure that the code will work during deployment and then run the production code. For this purpose, floop uses Docker to create runtime environments with all dependencies and code installed as needed.  

Both the test and run environments will run inside a virtual operating system on your target devices. This standardizes your test and production environments across devices, despite different underlying hardware and operating systems installed on that hardware.

Since testing often requires different dependencies and run behavior than a production environment, we will need one environment build file to test and another to run. 

.. tabs::

    .. tab:: C++ 

        First, define the test environment.
        
        We will start with a Debian Jessie operating system image, install a C++ compiler, install a testing library (Google Test), and set the default behavior of the environment to run the tests. 

        To accomplish these steps, add the following code to a file called **Dockerfile.test**:

        .. literalinclude:: ../../../example/src/cpp/Dockerfile.test
           
        At the end of the **Dockerfile.test** environment, it calls a script called **test.sh**. This script should compile all the code that needs to be tested, then run that code inside of the test environment.

        Add the following code to a file called **test.sh**:

        .. literalinclude:: ../../../example/src/cpp/test.sh

        Now when we run our floop tests, we will automatically re-compile all new code alongside our testing utilities, then run the tests.

        Next, define the run environment.

        As with the test environment, we will start with a Debian Jessie operating system image and install a C++ compiler. Unlike the test environment, we no longer need to install the testing library. We will also need to set the default behavior of the environment to run the code.

        To accomplish these steps, add the following code to a file called **Dockerfile**:

        .. literalinclude:: ../../../example/src/cpp/Dockerfile

        At the end of the **Dockerfile** environment, it calls a script called **run.sh**. This script should compile all the code that needs to be run then run that code inside of the run environment.

        Add the following code to a file called **run.sh**:

        .. literalinclude:: ../../../example/src/cpp/run.sh

        Now when we run our code, we will automatically re-compile all new code alongside our production utilities, then run the final binary.
        
        :subscript:`(Note: in a real production environment, you are usually better off using a runtime environment with minimal dependencies and running a pre-built executable. However, this is beyond the scope of Hello, World!)`

    .. tab:: Python 

        First, define the test environment.

        We will start with a Debian Jessie operating system with Python 3.6 already installed, then install a testing library (pytest), and set the default behavior of the environment to run tests.

        To accomplish these steps, add the following code to a file called **Dockerfile.test**:

        .. literalinclude:: ../../../example/src/python/Dockerfile.test

        At the end of the **Dockerfile.test** environment, it calls Python to run pytest on our project.

        Next, define the run environment.

        As with the test environment, we will start with a Debian Jessie operating system with Python 3.6 already installed. In this case, we have no external dependencies, so set the default behavior of the run environment to run Python on our **hello.py** entrypoint.

        To accomplish these steps, add the following code to a file called **Dockerfile**:

        .. literalinclude:: ../../../example/src/python/Dockerfile

    Now we are ready to build, test, and run our app with floop.

4. Configure the App with Floop
===============================
floop reads all project configuration from a single JSON configuration file. This configuration defines the details of source code, device network addresses, and initial authentication details.

We will use floop in order to generate a default configuration template and then modify that template to match our device and network configuration.

From within the **project** folder, run:
::
    floop config

This will generate a default configuration called **floop.json**.

This configuration is based on the following default values (this is a Python dictionary that gets written to JSON):

.. literalinclude:: ../../../floop/config.py
    :lines: 10-21

:subscript:`(Note: The calls to the *which* function automatically set the path of docker-machine and rsync as they are installed on your system. If needed, you can edit floop.json to set the paths to each binary dependency. This may be useful if you need to use a different version of docker-machine or rsync than the default version for your system.)`

floop looks for source code on your host computer at *host_source_directory*. You can change the value to point to the relative path of your source code from the **floop.json** file. For the purposes of this guide, the default **./src** should work if you run floop from the **project** directory.


When you run floop, it will automatically copy code from *host_source_directory* to *device_target_directory* on each target. For this guide, you should change *device_target_directory* depending on whether you are using Docker Machines on your host or hardware ARM devices.

.. tabs::

    .. tab:: ARM Devices 

        This is the option for using floop with real devices.

        For ARM devices, you need to update each entry in *devices*. For example, if you have a target device that you want to call *test0* that can be reached at IP address **192.168.188** and that device runs an operating system that has a user called *ubuntu* who uses **~/.ssh/floop.key** to SSH into your device, then you would configure floop as follows:

        ::

          ... # only showing non-default key-values
            'device_target_directory' : '/home/ubuntu/floop/',
            'devices' : [{
                  'address' : '192.168.1.188', 
                  'name' : 'test0',           
                  'ssh_key' : '~/.ssh/floop.key',
                  'user' : 'ubuntu'             
                },]
            }

        If you have more than one ARM device, then make sure to add entries to the *devices* list, changing the values to match the address, name, key, and operating system user for your specific device.

        For ARM devices, addresses should be unique.

    .. tab:: Docker Machines 

        This is the option for testing or evaluating floop before you use it with real devices.

        For Docker Machines on the host, if you have one existing Docker Machine called *floop0* then the default configuration should work for you. If you have more than one Docker Machine, then you should add more devices to the configuration, changing the value of *name* to the names you used when you created the devices. Note that floop will ignore all keys except for *name* if you use existing Docker Machines. To see existing Docker Machines on your host, use docker-machine directly to list them:
        ::

          docker-machine ls

Note that all device names must be unique. 

5. Create Floop Target Devices
==============================

Once you have a configuration file that defines your devices, you can create new floop devices by running:
::

  floop create

Optionally, you can add the *-v* flag to see what floop is doing under the hood to establish communication with your remote devices and handle encrypted authentication.

If you see any errors, follow the help messages that floop provides. Make sure that you have defined valid devices and that you have network access to those devices.

6. Push Code from Host to Targets
=================================
Once you have successfully created one or more floop devices, you can push code from your configured *host_source_directory* to *device_target_directory* by running:
::

  floop push

:subscript:`(Note: communication between the host and targets runs in parallel so floop works on all targets at the same time)`

Optionally, you can add the *-v* flag to see how floop uses rsync to synchronize the code between the host and all targets to ensure that the source and target are the same.

Your code is now on all of your targets so we can build, run, or test it.

7. Build Code on Targets
========================
In order to build you code on all of your targets, you can run:
::

  floop build

:subscript:`(Note: build uses Docker under the hood, so all builds are cached. This means that first build usually takes much longer than subsequent builds.)``

Optionally, you can add the *-v* flag to see that floop always pushes before a build then builds your run environment using the **Dockerfile** for your app. 

8. Test Code on Targets
======================
You can run your test environment for your app by running:
::

  floop test

Optionally, you can add the *-v* flag to see that floop always pushes and always builds and runs the test environment using the **Dockerfile.test** for your app.  

You should see your tests run on all targets.

9. Run Code on Targets
======================
You can run your run environment for your app by running:
::

  floop run 

Optionally, you can add the *-v* flag to see that floop always pushes and always builds and runs the run environment using the **Dockerfile** for your app.  

You should see all targets greet you with "Hello, World!"

10. Monitor Running or Testing Code on Targets
==============================================
If you have long-running tests or scripts that run indefinitely, you can check on all testing or running code on all targets by running:
::
 
  floop ps

Optionally, you can add the *-v* flag to see that floop calls Docker on all targets to determine which tests or runs are still running.

11. Log All Floop Events
========================
Once you push, build, test, and/or run code on your targets, you can see the logs from all targets directly on your host by running:
::

  floop logs

:subscript:`(Note: floop stores logs for each project in a file called floop.log in the root project folder. The logs contain sucessful commands as well as all errors messages.)`

Optionally, you can add the *-m* flag followed by a *match-term* to show only the lines of the log that contain *match-term*. 

For example, to show all lines that contain the term **TEST PASSED** you can run:
::

  floop logs -m "TEST PASSED"

12. Destroy Floop Target Devices
================================
When you are finished with this guide, you can destroy all the floop devices defined in your configuration file by running:
::

  floop destroy

:subscript:`(Note: floop destroys floop resources on all target devices and frees resources on the host. It does NOT remove your project or source from your host.)`

Optionally, you can add the *-v* flag to see that floop destroys devices by removing the *device_target_directory* from all targets, uninstalling Docker from all targets, and removing Docker Machines from the host.

If you followed this guide using more than one ARM device or Docker Machine, you may only want to destroy some of the floop devices you created before. In order to do this, you can remove all of the devices you want to destroy from your **floop.json** and add them to a new configuration file called **floop-destroy.json**. You can then destroy those devices using the *-c* flag for the floop command by running:
::

  floop -c floop-destroy.json destroy

This will free floop-related resources from the devices defined in **floop-destroy.json** while leaving the remaining devices in **floop.json** untouched.
