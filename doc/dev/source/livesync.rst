========
Livesync
========

.. automodule:: indico.ext.livesync

++++++++++++++++++++++
The Multipointer Track
++++++++++++++++++++++

.. currentmodule:: indico.ext.livesync.struct

The basic data structure used in ``livesync`` is the :py:class:`MultiPointerTrack` (MPT). It keeps all the information concerning changes that have been done to the data storage, and the curent status of each agent.

.. autoclass:: MultiPointerTrack
.. autoclass:: SetMultiPointerTrack


+++++++++++
SyncManager
+++++++++++

.. currentmodule:: indico.ext.livesync.agent

:py:class:`SyncManager` is basically a container for agents, and provides an interface for both agent management/querying and basic MPT manipulation.

.. autoclass:: SyncManager

++++++
Agents
++++++

So far, :py:class:`PushSyncAgent` is the only available agent type.

.. autoclass:: SyncAgent

.. autoclass:: PushSyncAgent

   .. automethod:: _generateRecords
   .. automethod:: _run

+++
CLI
+++

There is a Command-line interface available for ``livesync``. It can be easily invoked::

    jdoe $ indico_livesync
    usage: indico_livesync [-h] {destroy,list,agent} ...
    indico_livesync: error: too few arguments
    jdoe $

---------------
Listing the MPT
---------------

It is easy to obtain a listing of what is currently stored in the MPT::

    jdoe $ indico_livesync list
    12970820 <ActionWrapper@0x8df65ac (<MaKaC.conference.Contribution object at 0x8df65ec>) [data_changed,title_changed] 1297082086>
    12970819 <ActionWrapper@0x8df662c (<MaKaC.conference.Contribution object at 0x8df65ec>) [data_changed,title_changed] 1297081920>
    12970815 <ActionWrapper@0x8df666c (<MaKaC.conference.Contribution object at 0x8df65ec>) [data_changed] 1297081537>
    12970815 <ActionWrapper@0x8df66ac (<Conference 100994@0x8df67ac>) [data_changed] 1297081528>
    12970815 <ActionWrapper@0x8df66ec (<MaKaC.conference.Contribution object at 0x8df65ec>) [data_changed,created] 1297081528>
    12970815 <ActionWrapper@0x8df672c (<MaKaC.conference.Category object at 0x8e48dac>) [data_changed] 1297081517>
    12970815 <ActionWrapper@0x8df676c (<Conference 100994@0x8df67ac>) [data_changed,title_changed,created] 1297081517>

A query interval can also be specified (``]from, to]``)::

    jdoe $ indico_livesync list --from 12970816 --to 12970819
    12970819 <ActionWrapper@0x8db65ac (<MaKaC.conference.Contribution object at 0x8db65ec>) [data_changed,title_changed] 1297081920>
    jdoe $


+++++++++++++++++
Development Tools
+++++++++++++++++

In order to make life easier for plugin developers, we have included a few tools that make things simpler:

.. autoclass:: RecordUploader

   .. automethod:: _uploadBatch

+++++++++
Internals
+++++++++

.. automodule:: indico.ext.livesync.components
   :members:

.. automodule:: indico.ext.livesync.tasks
   :members:
