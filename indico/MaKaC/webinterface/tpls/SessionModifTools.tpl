<div class="toolsContainer">
    <div>
        <a href="${deleteSessionURL}" class="bs-btn-icon">
            <div  class="icon icon-remove icon-medium"></div>
            <div>${_("Delete")}</div>
        </a>
        ${ _("Deleting this session all the items under it will also be deleted")}
    </div>

    <div style="margin-top:5px;">
        <a href="${lockSessionURL}" class="bs-btn-icon">
            <div  class="icon icon-locked icon-medium"></div>
            <div>${_("Lock")}</div>
        </a>
        ${ _("Locking this session you will not be able to change its details any more")}
    </div>
</div>