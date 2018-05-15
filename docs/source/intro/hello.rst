.. _intro-hello:

===================
Hello, World! Guide
===================

Overview
========
**Estimated time to complete:**
    30 minutes

In this guide, you will:
    - develop a simple Hello, World! app in one of several languages 
    - configure floop with the app
    - create Docker environments on one or more target devices
    - push source code from your host device to target devices
    - build code on target devices
    - test code on target devices in a test operating system environment on the target
    - run code on target devices in a production operating system environment on the target

In the end, each target device should greet you with "Hello, World!"

If you have Linux-based target devices, you can use them for this guide. Otherwise, follow along to see how to use Docker Machines on your host to run and test floop using just your computer.

(Optional) Prerequisites
========================
- One or more ARM devices running a Linux-based operating system with `kernel version 3.10+ <https://docs.docker.com/engine/faq/#how-far-do-docker-containers-scale>`_. For example, `Orange Pi Zero <http://www.orangepi.org/orangepizero/>`_ running `Armbian <https://www.armbian.com/orange-pi-zero/>`_ mainline kernel.
    If you use target hardware, please make sure the operating system on each device follows the :ref:`intro-os`. 

0. Install Floop
================
Check out the :ref:`intro-install` here.

1. Develop a Simple App
====================
To start, we will make a simple app to print "Hello, World!" to the console. We will also add a small test suite to make sure our code works.

.. tabs::

    .. tab:: C++ 
    .. tab:: Python

        Make a new project folder with a src folder inside:
        ::
            mkdir -p ./project/src && cd ./project

        Add the following code to a file called **hello.py**:
        ::
            ### src/hello.py
            def hello():
                print('Hello, World!')

            if __name__ == '__main__':
                hello()

        Add the following code to a file called **hello_test.py**:
        ::
            ### src/hello_test.py
            from .hello import hello

            def test_hello():
                hello()

        In order for Python to consider our **src** folder as a package so that we can import code from **hello.py** into **hello_test.py**, add a blank file called **__init__.py**:
        ::
            touch ./src/__init__.py

        Test your code on the host:
        ::
            python ./src/hello.py

        You should see "Hello, World!" on the console.

Configure the App with Floop
============================
From within the **project** folder, run:
::
    floop config

This will generate a default configuration called **floop.json**.

Open **floop.json** in a text editor.
