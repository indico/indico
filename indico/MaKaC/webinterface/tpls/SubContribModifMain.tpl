<br>
<table width="90%" align="left" border="0">
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Title")}</span></td>
        <td bgcolor="white" class="blacktext" width="100%">${ title }</td>
        <form action="${ dataModificationURL }" method="POST">
        <td rowspan="4" valign="bottom" align="right" width="100%">
            <input type="submit" class="btn" value="${ _("modify")}">
        </td>
        </form>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Description")}</span></td>
        <td bgcolor="white" class="blacktext">
        ${ description }
      </td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Place")}</span></td>
        <td bgcolor="white" class="blacktext">${ place }</td>
    </tr>
    <tr>

        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Duration")}</span></td>
        <td bgcolor="white" class="blacktext">${ duration }</td>
    </tr>
    <tr>

        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Keywords")}</span></td>
        <td bgcolor="white" class="blacktext"><pre>${ keywords }</pre></td>
    </tr>
    <tr>
        <td colspan="3" class="horizontalLine">&nbsp;</td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Presenters")}</span></td>
        <td bgcolor="white" class="blacktext" colspan="2">
            <table width="100%">
                <tr>
                    <td style="width: 79%"><ul id="inPlaceSpeakers" class="UIPeopleList"></ul></td>
                    <td nowrap valign="top" style="width: 21%; text-align:right;">
                        <span id="inPlaceSpeakersMenu" onmouseover="this.className = 'mouseover'" onmouseout="this.className = ''">
                            <a class="dropDownMenu fakeLink"  style="margin-left: 15px; margin-right: 15px" onclick="speakerManager.addManagementMenu();">${ _("Add presenter") }</a>
                        </span>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
      <tr>
        <td colspan="3" class="horizontalLine">&nbsp;</td>
      </tr>
      % if Config.getInstance().getReportNumberSystems():
      <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Report numbers")}</span></td>
        <td bgcolor="white" colspan="2">${ reportNumbersTable }</td>
      </tr>
      % endif
</table>
<br>

<script>

var speakerManager = new SubContributionPresenterListManager('${ confId }',
        {confId: '${ confId }', contribId: '${ contribId }', subContribId: '${ subContribId }'},
        $E('inPlaceSpeakers'), $E('inPlaceSpeakersMenu'), "presenter", ${presenters | n,j}, ${authors | n,j}, '${ eventType }');

</script>
