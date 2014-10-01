Hooking into Indico using Signals
=================================

Signals allow you to hook into certain parts of Indico without
adding any code to the core (which is something a plugin can and
should not do). Each signal has a *sender* which can be any object
(depending on the signal) and possibly some keyword arguments.
Some signals also make use of their return value or even require
one. Check the documentation of each signal on how it's used.

To avoid breakage with newer versions of Indico, it is highly
advised to always accept extra ``**kwargs`` in your signal receiver.
For example, a receiver function could look like this::

    def receiver(sender, something, **kwargs):
        do_stuff_with(something)


.. autodata:: indico.core.signals.cli
   :annotation:
.. autodata:: indico.core.signals.shell_context
   :annotation:
.. autodata:: indico.core.signals.get_blueprints
   :annotation:
.. autodata:: indico.core.signals.inject_css
   :annotation:
.. autodata:: indico.core.signals.inject_js
   :annotation:
.. autodata:: indico.core.signals.event_management_sidemenu
   :annotation:
