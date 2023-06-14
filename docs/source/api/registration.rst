Registration
============

Introduction
++++++++++++

The Registration Form module relies on a data model which can be slightly complex at a first glance, due to the
basic "version control" of fields which Indico does, in order to allow for modifications after users have registered.

.. mermaid::

    classDiagram
        class RegistrationData {
            data
        }
        class RegistrationFormFieldData {
            versioned_data
        }

        RegistrationForm --o RegistrationFormItem
        RegistrationFormItem --o RegistrationFormItem : children
        RegistrationForm --o Registration
        Registration "1" --o RegistrationData : field_data
        RegistrationFormFieldData "1" --o RegistrationData
        RegistrationFormFieldData "1" -- "1" RegistrationFormItem : current_data
        RegistrationFormItem "1" --o RegistrationFormFieldData : data_versions

Some notes on these model classes:

 * :class:`~indico.modules.events.registration.models.forms.RegistrationForm` - the actual registration form. There can
   be several per event;
 * :class:`~indico.modules.events.registration.models.items.RegistrationFormItem` - those can be fields or sections
   (personal or not). Sections can contain "children" (fields). They specialize into
   :class:`~indico.modules.events.registration.models.form_fields.RegistrationFormField`,
   :class:`~indico.modules.events.registration.models.form_fields.RegistrationFormPersonalDataField`,
   :class:`~indico.modules.events.registration.models.items.RegistrationFormSection` and
   :class:`~indico.modules.events.registration.models.items.RegistrationFormPersonalDataSection`;
 * :class:`~indico.modules.events.registration.models.registrations.Registration` - someone's registrations at an
   event, in a given registration form;
 * :class:`~indico.modules.events.registration.models.form_fields.RegistrationFormFieldData` - this represents the
   state of the "configuration" of a form item at a given point in time;
 * :class:`~indico.modules.events.registration.models.registrations.RegistrationData` - this class "links" a
   ``RegistrationFormFieldData`` and a ``Registration`` together. It is the registration's "value" for a field at a
   given "configuration" state.


.. automodule:: indico.modules.events.registration


Models
++++++

.. automodule:: indico.modules.events.registration.models.registrations
    :members:
    :undoc-members:

.. automodule:: indico.modules.events.registration.models.form_fields
    :members:
    :undoc-members:

.. automodule:: indico.modules.events.registration.models.forms
    :members:
    :undoc-members:

.. automodule:: indico.modules.events.registration.models.invitations
    :members:
    :undoc-members:

.. automodule:: indico.modules.events.registration.models.items
    :members:
    :undoc-members:


Utilities
+++++++++

.. automodule:: indico.modules.events.registration.util
    :members:
    :undoc-members:


Placeholders
++++++++++++

.. automodule:: indico.modules.events.registration.placeholders.registrations
    :members:
    :undoc-members:

.. automodule:: indico.modules.events.registration.placeholders.invitations
    :members:
    :undoc-members:


Settings
++++++++

.. automodule:: indico.modules.events.registration.settings
    :members:
    :undoc-members:


Statistics
++++++++++

.. automodule:: indico.modules.events.registration.stats
    :members:
    :undoc-members:
