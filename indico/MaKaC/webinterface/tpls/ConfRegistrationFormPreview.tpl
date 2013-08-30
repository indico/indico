<div id="headPanel" style="box-shadow: 0 4px 2px -2px rgba(0, 0, 0, 0.1); z-index: 100;" class="follow-scroll" style="z-index:1300;">
            <table>
                <tr >
                    <td valign="bottom" align="left">
                        <ul id="button-menu" class="ui-list-menu">
                          <li class="left" >
                              <a href="#" id="section_create">${ _("Create section")}</a>
                          </li>
                          <li class="middle" >
                              <a href="#" id="sections_mgmt">${ _("Recover/Discard sections")}</a>
                          </li>
                          <li class="middle">
                            <a href="#" id="collapse_all">${ _("Collapse All")}</a>
                          </li>
                          <li class="right">
                            <a href="#" id="expand_all">${ _("Expand All")}</a>
                          </li>
                        </ul>
                    </td>
                </tr>
            </table>
    </div>
    <div id="registrationForm" class="sortableForm"></div>
    <div id="edit-popup"></div>
    <div id="section-mgmt-popup" style="max-height : 500px;"></div>
    <div id="section-create-popup"></div>

<script type="text/javascript">
    $.webshims.polyfill();
    $(document).ready(function(){
        var confId = ${ confId };
        var rfView = new RegFormEditionView({ el : $("div#registrationForm")});
        var model = rfView.getModel();
        var sectionsMgmt = new RegFormSectionsMgmtView ({el : $('#section-mgmt-popup'), model : model});
        var sectionCreate = new RegFormSectionsCreateView ({el : $('#section-create-popup'), model : model});

        // Create drop down menu
        $('#button-menu').dropdown();
        $(window).scroll(function(){
            IndicoUI.Effect.followScroll();
        });
        // Menu function
        $("#collapse_all").click(function(){
            $("div.regFormSectionContent:visible").slideUp("slow");
            $(".regFormButtonCollpase").button( "option", "icons", {primary:'ui-icon-triangle-1-w'} );
        });
        $("#expand_all").click(function(){
            $("div.regFormSectionContent:hidden").slideDown("slow");
            $(".regFormButtonCollpase").button( "option", "icons", {primary:'ui-icon-triangle-1-s'} );
        });
        $("#sections_mgmt").click(function(){
            sectionsMgmt.show();
        });
        $("#section_create").click(function(){
            sectionCreate.show();
        });
    });
</script>
