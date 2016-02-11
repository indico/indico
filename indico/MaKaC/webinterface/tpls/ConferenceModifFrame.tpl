<%
from MaKaC.webinterface.urlHandlers import UHConferenceModification
%>

<div class="banner">

    ${ template_hook('event-manage-header', event=conf) }

    <a href="${ UHConferenceModification.getURL(conf) }">
        <span class="bannerTitle bannerTitle_0">
            ${ conf.getTitle() | remove_tags } &nbsp;<span style="font-size: 0.8em; font-style: italic;">
            % if startDate == endDate:
                ${ startDate }
            % else:
                ${ startDate } - ${ endDate }
            % endif
            </span>
        </span>
    </a>
    <div class="banner_creator">
        ${ _(u"Created by {name} ({email})").format(name=conf.as_event.creator.full_name, email=conf.as_event.creator.email)}
    </div>

</div>

<div class="layout-sidemenu">
    <div id="event-sidemenu" class="sidemenu">${ sideMenu }</div>
    <div class="body">
        ${ render_template('flashed_messages.html') }
        ${ body }
    </div>
</div>
