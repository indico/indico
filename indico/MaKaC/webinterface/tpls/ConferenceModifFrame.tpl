<%
from MaKaC.webinterface.urlHandlers import UHConferenceModification
%>

<div class="banner">

    <div class="title">
        <a href="${ UHConferenceModification.getURL(conf) }">
            ${ conf.getTitle() | remove_tags } &nbsp;
            <span class="date">
                % if startDate == endDate:
                    ${ startDate }
                % else:
                    ${ startDate } - ${ endDate }
                % endif
            </span>
        </a>
        <div class="subtitle">
            ${ _(u"Created by {name} ({email})").format(name=conf.as_event.creator.full_name, email=conf.as_event.creator.email)}
        </div>
    </div>

    ${ template_hook('event-manage-header', event=conf) }

</div>

<div class="layout-sidemenu">
    <div id="event-sidemenu" class="sidemenu">${ sideMenu }</div>
    <div class="body">
        ${ render_template('flashed_messages.html') }
        ${ body }
    </div>
</div>
