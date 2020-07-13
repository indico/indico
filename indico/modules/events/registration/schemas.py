from marshmallow.fields import Integer, String

from indico.core.marshmallow import mm
from indico.modules.events.registration.models.forms import RegistrationForm


class RegistrationFormSchema(mm.ModelSchema):
    class Meta:
        model = RegistrationForm
        fields = ('id', 'name', 'identifier')

    id = Integer(attribute='id')
    name = String(attribute='title')
    identifier = 'RegistrationForm:{}'.format(id)
