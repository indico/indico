<div style="padding:20px 0px">

<form action="${ urlHandlers.UHConfAbstractBook.getURL( conf ) }" method="POST">
<input type="submit" class="btn" name="createAbstractsBook" value="Create book of abstracts now" />
</form>
<br /><br />
% if bookOfAbstractsActive:
    % if bookOfAbstractsMenuActive:
        Note that your customizations will be saved and users will be able to download this book of abstract from the <a href="${ urlHandlers.UHConferenceDisplay.getURL( conf ) }">event home page</a>.
    % else:
        Note that you need to enable the book of abstracts link in <a href="${ urlHandlers.UHConfModifDisplayMenu.getURL( conf ) }">Layout->Menu</a>.
    % endif
% else:
    Note that you need to enable call for abstracts if you wish to provide a link in the <a href="${ urlHandlers.UHConferenceDisplay.getURL( conf ) }">event home page</a> menu, so users can download your book of abstracts.
% endif
</div>

<div class="groupTitle">${ _("Customisation")}</div>
<table width="90%" align="center" border="0">
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Additional text")}</span></td>
        <td>
            <div class="blacktext" id="inPlaceEditAdditionalText">${ text }</div>
        </td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Sort by")}</span></td>
        <td class="blacktext" width="100%">
            <div id="inPlaceEditSortBy" style="display:inline"></div>
        </td>
    </tr>
    <tr>
        <td class="dataCaptionTD">
            <span class="dataCaptionFormat"> ${ _("Miscellaneous options")}</span><br/><br/>
            <img src="${Config.getInstance().getSystemIconURL( 'enabledSection' )}" alt="${ _("Click to disable")}"> <small> ${ _("Enabled option")}</small>
            <br />
            <img src="${Config.getInstance().getSystemIconURL( 'disabledSection' )}" alt="${ _("Click to enable")}"> <small> ${ _("Disabled option")}</small>
            <br />
        </td>
        <td bgcolor="white" width="100%" class="blacktext">
            % if showIds:
                <% icon = str(Config.getInstance().getSystemIconURL( "enabledSection" )) %>
            % else:
                <% icon = str(Config.getInstance().getSystemIconURL( "disabledSection" )) %>
            % endif
            <a href="${urlToogleShowIds}"><img src="${icon}"> ${_("Show Abstract IDs")}</a> ${_("(Table of Contents)")}
            <br/>
        </td>
    </tr>
</table>
<script type="text/javascript">

<%  from MaKaC.common import info %>
$E('inPlaceEditAdditionalText').set(new RichTextInlineEditWidget('abstract.abstractsbook.changeAdditionalText', ${ jsonEncode(dict(conference="%s"%conf.getId())) }, ${ jsonEncode(text) }, 300, 45).draw());
new IndicoUI.Widgets.Generic.selectionField($E('inPlaceEditSortBy'), 'abstract.abstractsbook.changeSortBy', ${dict(conference="%s"%conf.getId())}, ${sortByList}, '${sortBy}');
</script>


