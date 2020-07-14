from marshmallow.fields import String

from indico.core.marshmallow import mm
from indico.modules.events.registration.models.forms import RegistrationForm


class RegistrationFormSchema(mm.ModelSchema):
    class Meta:
        model = RegistrationForm
        fields = ('id', 'name', 'identifier')

    name = String(attribute='title')
    identifier = String()
