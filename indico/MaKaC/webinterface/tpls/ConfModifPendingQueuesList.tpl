% if list:
<div id="actionsToolbar" class="bs-alert alert-toolbar">
    <form action="${ postURL }" method="post">
    <input type="submit" class="btn btn-right btn-primary" name="remove" value="${ _("Remove Selected")}" />
    <input type="submit" class="btn btn-right" name="reminder" value="${ _("Send a Reminder")}" />
    <div>
        ${title}
    </div>
    <div style="padding-top:5px;">
        <span class="fakeLink" id="selectAllEntries">${_('Select All')}</span> -
        <span class="fakeLink" id="selectNoEntries">${_('Select None')}</span>
    </div>
    <div class="toolbar-clearer"></div>
</div>
<div>
    % for (key, pList) in list:
    <div class="speakerEntry">
        <div class="speakerDetails">
            <input type="checkbox" name="pendingSubmitters" value="${str(key)}">
            ${pList[0].getFullName()} - (${pList[0].getEmail()})
        <% pList.sort(self_._cmpByContribName) %>
        </div>
        <div class="speakerContributions">
            <ol>
        % for cp in pList:
                <li>
            <% contrib = cp.getContribution() %>
                    <a href="${str(urlHandlers.UHContributionModification.getURL(contrib))}">
                        ${contrib.getTitle()}
                    </a>
            % if pType == _("Submitters"):
                % if contrib.isPrimaryAuthor(cp):
                    ${_("Primary Author")}
                % elif contrib.isCoAuthor(cp):
                    ${_("Co-Author")}
                % elif contrib.isSpeaker(cp):
                    ${_("Speaker")}
                % endif
            % endif
                </li>
        % endfor
            </ol>
        </div>
    </div>
    % endfor
    </form>
</div>
% else:
<p>
    ${_('There are no pending requests at this time.')}
</p>
% endif

<script type="text/javascript">

$(document).ready(function() {
    $('#selectAllEntries').click(function() {
        $('.speakerDetails input').prop('checked', true);
    });

    $('#selectNoEntries').click(function() {
        $('.speakerDetails input').prop('checked', false);
    });
});

</script>
