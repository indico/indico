<%inherit file="Footer.tpl"/>
<%block name="footer_classes">footerCERN</%block>
<%block name="footer">
    <a id="cern_link" href="http://cern.ch">
        <img src="${ systemIcon("cern_small_light" if is_meeting else "cern_small") }" alt="${ _("Indico")}" class="cern_logo" style="vertical-align: middle; margin: 15px;">
    </a>
    <div class="text" style="width: 200px">
        ${ _("Powered by ")} <a href="http://indico-software.org">Indico</a>
        ${ template_hook('page-footer') }
    </div>
</%block>
