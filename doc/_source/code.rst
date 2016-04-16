Code
====

fitbit
------

.. automodule:: recover.fitbit
    :members:

models
------

.. automodule:: recover.models
    :members:

patient_data
------------

.. automodule:: recover.patient_data
    :members:

EmailClient
-----------

.. automodule:: recover.EmailClient
    :members:

Graphing
--------
Our Graphing Utility uses JavaScript and Vis.js. We implemented a Double Exponential Smoothing algorithm
for trends.

.. js:function:: FitBitGraphing(heartRateData, averageHeartRate, stepsData, start, end)

   :param dict heartRateData: All heart rate data for a patient to display onto the graph.
   :param dict averageHeartRate: Separated out average heart rate data.
   :param dict stepsData: All Activity data for a patient to display onto the activity graph.
   :param start: Time stamp for the left-most point on the initial x axis.
   :param end: Time stamp for the right-most point on the initial x axis.

.. js:function:: setup(data, group_start, inner_group)

   :param dict data: One of the data dicts to format for display.
   :param int group_start: Group ID.
   :param bool inner_group: Decided whether or not to recursively group.
   :return: A formatted list for vis.js

.. js:function:: trend(data_arr, n_groups)

   :param list data_arr: data to smooth
   :param int n_groups: grouping information

.. js:function:: grouping(data)

   :param data: data to further group

.. js:function:: clone(obj)

   :param obj: Object to clone


