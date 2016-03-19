<%page args="protection=None"/>
<div id="protectionWidget" style="display:none" class="protectionWidget">
    <div class="protectionWidgetSection">
        % if protection[0] == "DomainProtected":
            ${_("The information on this web page is restricted for display on the %s") % protection[1]}
        % elif protection[0] == "Public":
            ${_("The information on this web page is visible to anyone")}
        % else:
            ${_("The information on this web page is restricted for display to named individuals or specific groups.")}
        % endif
    </div>
    <div class="protectionWidgetSection">
        % if protection[0] == "DomainProtected":
            ${protectionDisclaimerProtected}
        % elif protection[0] == "Restricted":
            ${protectionDisclaimerRestricted}
        % endif
    </div>
    <div class="protectionWidgetSection">
        <div><a href="http://indico.cern.ch/ihelp/html/UserGuide/Protection.html" target="blank">${ _("Learn more about Indico and Security") }</a></div>
    </div>
</div>

<a id="protectionLink" class="${'icon-shield' if protection[0] != 'Public' else 'icon-earth'} arrow i-button protection-${protection[0].lower()}">${protection[1]}</a>


<script type="text/javascript">
$("#protectionLink").qtip({

    style: {
        width: '280px',
        classes: 'qtip-rounded qtip-shadow qtip-popup',
        tip: {
            corner: true,
            width: 20,
            height: 15
        }
    },
    position: {
        my: 'top center',
        at: 'bottom center'
    },
    content:  $('#protectionWidget'),
    show: {
        event: "click",
        effect: function() {
            $(this).fadeIn(300);
        }
    },
    hide: {
        event: 'unfocus click',
        fixed: true,
        effect: function() {
            $(this).fadeOut(300);
        }
    }
});
</script>
