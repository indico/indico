<div class="groupTitle"> ${ _("Instance Tracking settings") }</div>

<form action="${ postURL }" method="POST">

    <div class="instanceTrackingSettings">
        <div class="clearfix">
            <span class="dataCaptionFormat">${ enableDisable }</span>
            <a href="${ toggleURL }">
                <img src="${ imgURL }" border="0" style="float:left; padding-right: 5px">${ _("Receive important notifications") }
            </a>
        </div>
        <div class="clearfix">
            <span class="dataCaptionFormat">${ _("Contact person name") }</span>
            <input type="text" name="contact" value="${ contact }">
        </div>
        <div class="clearfix">
            <span class="dataCaptionFormat">${ _("Contact email address") }</span>
            <input type="text" name="email" value="${ email }">
        </div>
        <div class="clearfix">
            <input type="submit" class="btn" name="cancel" value="${ _("Cancel")}">
            <input type="submit" class="btn" name="save" value="${ _("Save")}">
        </div>
    </div>

</form>
