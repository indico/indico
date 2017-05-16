Hooking into Indico using Signals
=================================

.. contents::
    :depth: 3

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


indico.core.signals
-------------------

.. exec::
    def main():
        from types import ModuleType
        from blinker import Signal
        from indico.core import signals

        separators = ['+', '*', '^', '\'']

        def generate_signal_doc(module, nesting=0):

            sorted_attributes = sorted(
                ((getattr(module, n), n) for n in dir(module)),
                key=lambda (a, n): (isinstance(a, ModuleType), module.__name__, n)
            )
            for attr, name in sorted_attributes:
                if isinstance(attr, Signal):
                    print '.. autodata:: {}.{}'.format(module.__name__, name)
                    print '   :annotation:'

                # core is always imported in __init__.py and
                # event.__init__.py always import its submodules directly so we
                # don't recurse in those cases to avoid duplicate docs
                elif (isinstance(attr, ModuleType) and
                        name != 'core' and module.__name__ != 'indico.core.signals.event'):
                    print attr.__name__
                    print separators[nesting] * len(attr.__name__)
                    generate_signal_doc(attr, nesting=(nesting + 1))

        generate_signal_doc(signals)

    main()
