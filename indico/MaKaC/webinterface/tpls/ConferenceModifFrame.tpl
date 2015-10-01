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

<table cellpadding="0" cellspacing="0" style="width:100%">
    <tbody>
        <tr>
            <td style="vertical-align: top; width:200px" id="event-sidemenu">${ sideMenu }</td>
            <td style="vertical-align: top">
                <div class="body" style="padding:20px;">
                    ${ render_template('flashed_messages.html') }
                    ${ body }
                </div>
            </td>
        </tr>
    </tbody>
</table>
