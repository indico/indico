<div style="border-bottom: 1px solid #EAEAEA; padding-bottom: 5px; margin-bottom: 15px;">
    % if abstracts:
    <form action="${str(urlHandlers.UHUserAbstractsPDF.getURL(conf))}" method="post" target="_blank" id="formAbstracts">
        <span class="fakeLink" id="exportPDF">${ _("Export to PDF")}</span>
    </form>
    % else:
        <span class="collShowBookingsText">${_("No submitted abstract found within this conference")}</span>
    % endif
</div>
<div id="abstractList">
    % for abstract in abstracts:
    <div class="abstractListAbstractItem">
        <div>
            <a href="${str( urlHandlers.UHAbstractDisplay.getURL( abstract ))}" style="font-size:14px">${abstract.getTitle()} </a>
        </div>
        <div style="line-height:17px; font-size: 12px; color:#666666;">
            <div style="display:inline"><span style="font-weight:bold">${_("Id")}: </span>${abstract.getId()}</div>
            <div style="display:inline"><span style="font-weight:bold">${_("Status")}: </span>${getAbstractStatus(abstract)}</div>
            <div style="display:inline"><span style="font-weight:bold">${_("Last modified")}: </span>${formatDate(abstract.getModificationDate()) + " "+ formatTime(abstract.getModificationDate())}</div>
        </div>
    </div>
    % endfor
</div>

<script type="text/javascript">
IndicoUI.executeOnLoad(function(){
    $("#exportPDF").click(function(){
        $("#formAbstracts").submit();
    });
});
</script>