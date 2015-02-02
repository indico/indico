from flask import render_template

from indico.modules.rb.models.locations import Location

from MaKaC.authentication.AuthenticationMgr import AuthenticatorMgr
from MaKaC.webinterface.common import tools as security_tools
from MaKaC.export import fileConverter
from MaKaC.webinterface import urlHandlers
from MaKaC.webinterface.materialFactories import MaterialFactoryRegistry


def generate_global_file(config):

    locations = Location.find_all() if config.getIsRoomBookingActive() else []
    default_location = next((loc.name for loc in locations if loc.is_default), None)
    ext_auths = [(auth.id, auth.name) for auth in AuthenticatorMgr().getList() if auth.id != 'Local']
    file_type_icons = dict((k.lower(), v[2]) for k, v in config.getFileTypes().iteritems())
    material_types = dict((evt_type, [(m, m.title()) for m in MaterialFactoryRegistry._allowedMaterials[evt_type]])
                          for evt_type in ['meeting', 'simple_event', 'conference', 'category'])

    return render_template(
        'assets/vars_globals.js',
        config=config,
        default_location=default_location,
        ext_authenticators=ext_auths,
        file_converter=fileConverter,
        locations={loc.name: loc.name for loc in locations},
        material_types=material_types,
        security_tools=security_tools,
        file_type_icons=file_type_icons,
        urls=urlHandlers
    )
