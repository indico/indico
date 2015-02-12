(function(global) {
    "use strict";

    var default_i18n = new Jed({
        locale_data: TRANSLATIONS,
        domain: "indico"
    });

    global.i18n = default_i18n;
    global.$T = _.bind(default_i18n.gettext, default_i18n);

    ['gettext', 'ngettext', 'pgettext', 'npgettext', 'translate'].forEach(function(method_name) {
        global.$T[method_name] = _.bind(default_i18n[method_name], default_i18n);
    });

    global.$T.domain = _.memoize(function(domain) {
        return new Jed({
            locale_data: TRANSLATIONS,
            domain: domain
        });
    });
}(window));
