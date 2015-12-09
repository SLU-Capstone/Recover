Recover: Cardiovascular Tracking System
=======================================


Introduction
------------

While consumer-based health and fitness trackers are becoming increasingly popular, they are not yet incorporated into
post-operative health care in any standardized way. This research project aims to bridge this gap, using commercially
available fitness devices to tighten the feedback loop between physicians and patients.

The goal of this project is to develop a web application that allows one or more physicians to follow the progress of
a recovering patient after they have been discharged from a clinic or hospital after a cardiovascular operation.
Through the application, a physician will be able to view a patient’s biometric data over time (i.e. heart rate,
activity, and sleep) collected by the patient’s Fitbit wearable device with heart-rate monitoring capabilities.
Using such a system gives the physician the ability to gain insight into the patient’s heart rate and cardiovascular
activity -- down to minute-level resolution -- over a span of weeks following an operation. This will ensure that the
physician can make necessary changes to the patient’s recovery plan if certain variations occur. The physician then
can gain a more complete picture of the patient’s activity variability over a span of weeks. This information
supplements the health assessment of the patient rather than only having a single point of care interaction with which
to base all data from.


Usage
-----

This project primarily uses Flask_ and extensions of Flask for the web application and MongoDB_ as the database
for our storage. Full source code is available from our `GitHub repository`_.

To use, clone our repository and cd into it and download dependencies::

    git clone https://github.com/SLU-Capstone/Recover.git
    cd Recover/
    pip install -r requirements.txt

Now, to selfhost the application::

    python manage.py run

You should now have a copy of the web application at 127.0.0.1:5000

.. _Flask: http://flask.pocoo.org/
.. _MongoDB: https://www.mongodb.org/
.. _GitHub repository: https://github.com/SLU-Capstone/Recover
