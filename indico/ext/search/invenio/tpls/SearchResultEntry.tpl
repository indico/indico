<%page args="accessWrapper=None, result=None"/>
<% import MaKaC %>

<li class="${"searchResultEvent" if type(result) == ConferenceEntry else "searchResultContribution"}">
    % if result.getTitle():
        <a class="searchResultTitle" href="${ result.getURL().replace('%','%%') }">${ result.getTitle() }</a>
    % endif
    % if result.getStartDate(accessWrapper):
         <small style="display: block;">${ result.getStartDate(accessWrapper).strftime("%Y-%m-%d %H:%M:%S (%Z)") }</small>
    % endif
    % if not isinstance(result.getTarget(),MaKaC.conference.Conference):
         <span style="display: block; font-style:italic; font-size:x-small;">${ result.getConference().getTitle()}</span>
    %endif
    <ul class="authorList">
        % for author in result.getAuthors():
            <li ${'class="last"' if author == result.getAuthors()[-1] else ""}>
                ${ author.getName() }
                <small>(${ author.getRole() } ${", %s"%author.getAffiliation() if author.getAffiliation() else ""})</small>
            </li>
        % endfor
    </ul>

<%
if result.getDescription() != None:
    fullDesc = result.getDescription()
    entryDesc = truncateTitle(result.getDescription(), maxSize=100)
else:
    fullDesc = entryDesc = ''
%>

    <div class="searchResultDescription">
        ${ entryDesc }
        % if len(entryDesc) < len(fullDesc):
            <a href="#" class="searchResultLink" onclick="IndicoUI.Effect.appear($E('desc${ result.getCompoundId() }')); $E(this).getParent().getParent().remove($E(this).getParent()); return false;" style="margin-bottom: 10px;">more</a>
        % endif
    </div>

    <div id='desc${ result.getCompoundId() }' class="searchResultDescription" style="display: none;">
        ${ fullDesc }
    </div>

    <ul class="nobulletsListInline" style="margin-top: 5px; margin-left: 20px;">
        % for material in result.getMaterials():
        <li><a class="searchResultLink" href="${ material[0] }">${ material[1] }</a></li>
        % endfor
    </ul>
</li>