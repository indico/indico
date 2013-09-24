<div id="headPanel" class="follow-scroll">
  <div class="toolbar">
        <div class="group">
            <a href="#" class="i-button icon-plus" id="section_create" title="${ _('Create section')}"></a>
            <a href="#" class="i-button" id="sections_mgmt">${ _("Recover/Discard sections")}</a>
            <a href="#" class="i-button icon-stack-plus" id="expand_all" title="${ _('Expand All')}"></a>
            <a href="#" class="i-button icon-stack-minus" id="collapse_all" title="${ _('Collapse All')}"></a>
        </div>
  </div>
</div>
    <div id="registrationForm" class="sortableForm"></div>
    <div id="edit-popup"></div>
    <div id="section-mgmt-popup" style="max-height : 500px;"></div>
    <div id="section-create-popup"></div>
    <input type="hidden" value="${confId}" id="conf_id">

<script type="text/javascript">
    $('#registrationForm').html(progressIndicator(false, true).dom);
    $.webshims.polyfill();
    $(function(){
        var confId = ${confId};
        var rfView = new RegFormEditionView({el: $("div#registrationForm")});
        var model = rfView.getModel();
        var sectionsMgmt = new RegFormSectionsMgmtView({el: $('#section-mgmt-popup'), model: model});
        var sectionCreate = new RegFormSectionsCreateView({el: $('#section-create-popup'), model: model});

        $(window).scroll(function(){
            IndicoUI.Effect.followScroll();
        });
        // Menu function
        $("#collapse_all").click(function(){
            $("div.regFormSectionContent:visible").slideUp("slow");
            $(".regFormButtonCollpase").button( "option", "icons", {primary: 'ui-icon-triangle-1-w'});
        });
        $("#expand_all").click(function(){
            $("div.regFormSectionContent:hidden").slideDown("slow");
            $(".regFormButtonCollpase").button("option", "icons", {primary: 'ui-icon-triangle-1-s'});
        });
        $("#sections_mgmt").click(function(){
            sectionsMgmt.show();
        });
        $("#section_create").click(function(){
            sectionCreate.show();
        });
    });
</script>
