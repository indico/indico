<!-- CONTEXT HELP DIVS -->
<div id="tooltipPool" style="display: none">
    <div id="eventsVisibilityHelp" class="tip">
        ${ _("""<b>Indicates when events from this category are shown in the event overview webpage.</b><br>
        - <b>Everywhere</b>: events are shown in the event overview webpage for this category and the parent categories<br>
        - <b>""" + name + """</b>: events are shown only in the overview webpage for this category (""" + name + """)<br>
        - <b>Nowhere</b>: events are not shown in any overview webpage.""")}
    </div>
</div>
<!-- END OF CONTEXT HELP DIVS -->

<form action="${ postURL }" method="POST" ENCTYPE="multipart/form-data">
    <table class="groupTable">
        <tr>
            <td colspan="2"><div class="groupTitle">
                     ${ _("Modification of category basic data")}
            </div>
            </td>
        </tr>
        <tr>
            <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Name")}</span></td>
            <td class="blacktext"><input type="text" name="name" size="50" value="${ name }"></td>
        </tr>
        <tr>
            <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Description")}</span></td>
            <td class="blacktext">
                <textarea name="description" cols="43" rows="6">${ description }</textarea>
            </td>
        </tr>
        <tr>
            <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Icon")}</span></td>
            <td class="blacktext">
                ${ icon }
        <input type="submit" class="btn" name="delete" value="${ _("delete")}">
                <br><input type="file" name="icon">
            </td>
        </tr>
        <tr>
            <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Default lectures style")}</span></td>
            <td class="blacktext"><select name="defaultSimpleEventStyle">${ simple_eventStyleOptions }</select></td>
        </tr>
        <tr>
            <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Default meetings style")}</span></td>
            <td class="blacktext"><select name="defaultMeetingStyle">${ meetingStyleOptions }</select>
            <input type=checkbox name="subcats" value=True> ${ _("Same style in all subcategories")}</td>
        </tr>
        <tr>
            <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Event visibility")}</span></td>
            <td class="blacktext">
              <select name="visibility">
              ${ visibility }
              </select>
              ${contextHelp('eventsVisibilityHelp')}
              </td>
        </tr>
        <tr>
            <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Disable suggestions")}</span></td>
            <td class="blacktext">
                % if user.isAdmin():
                <input name="disableSuggestions" type="checkbox" ${'checked="checked"' if rh._target.isSuggestionsDisabled() else ''}}>
                ${inlineContextHelp(_('If checked, the category will not be suggested as a potential favorite in the dashboard.'))}
                % else:
                <input name="disableSuggestions" type="checkbox" disabled="disabled" ${'checked="checked"' if rh._target.isSuggestionsDisabled() else ''}}>
                ${inlineContextHelp(_('If checked, the category will not be suggested as a potential favorite in the dashboard. Only Indico administrators may change this settings.'))}
                % endif
            </td>
        </tr>
        <tr>
            <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Default Timezone")}</span></td>
            <td class="blacktext"><select name="defaultTimezone">${ timezoneOptions }</select>
            % if not rh._target.getSubCategoryList():
            <input type=checkbox name="modifyConfTZ" value=False>${ _("Modify timezone for all conferences")}</td>
            % endif
        </tr>
    <tr>
            <td>&nbsp;</td>
            <td class="blacktext">
                <input type="submit" class="btn" name="OK" value="${ _("ok")}">
                <input type="submit" class="btn" name="cancel" value="${ _("cancel")}">
            </td>
        </tr>
    </table>
</form>
