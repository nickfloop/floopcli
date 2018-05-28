floop
=====

.. image:: http://docs.forward-loop.com/floopcli/ec2/status/build-status.png
   :target: http://docs.forward-loop.com/floopcli/ec2/status/build-status.html

Note: this repository is in the alpha development stage. We recommend you always pull or upgrade to the latest version. 

floop is a CLI tool for developing, building, and testing code on
multiple target devices using a single host device. Currently, the tool
works for Linux targets, including many ARM devices.

Documentation
-------------

Please visit `the official floop documentation <http://docs.forward-loop.com/floopcli/master/index.html>`_ for tutorials, guides,
and more information.

You can see more Forward Loop projects and documentation at `our
documentation website <http://docs.forward-loop.com>`_.

Learn more about Forward Loop at our `company website <http://forward-loop.com>`_.

Installation
------------
You can download the latest official release as a pip package:
::

    pip install --upgrade floopcli

For developing floopcli itself, you can pull this repository and install it locally with pip:
::

    git clone git@github.com:ForwardLoopLLC/floopcli.git && cd floopcli && pip install -e .[test] 

Testing
-------

floop has been tested on multiple ARM devices running Linux operating
systems. Additionally, floop has its own continuous integration
platform, which you can learn about by visting the **ci/** folder in
this repository.

Contributing
------------

floop is an open-source project from Forward Loop LLC. We encourage
community engagement. If you find any bugs or want to propose new
features, please raise an issue in this repository.
