<%page args="protection=None"/>
<div id="protectionWidget" style="display:none" class="protectionWidget">
    <div class="protectionWidgetSection">
        <div>${_("The information here displayed is")}
        <span class="protectionHighlight${protection[0]}">${protection[1].upper()}</span><br/></div>
        <div style="padding-top:10px; text-align:justify">
            ${_("""The elements on this page are no viewable by the general public. The <a href="https://security.web.cern.ch/" target="blank">CERN Security Policy</a> binds you to treat such data confidientially as denoted in the policy itself.""")}
        </div>
    </div>
    <div class="protectionWidgetSection">
        <div><a href="http://indico.cern.ch/ihelp/html/UserGuide/Protection.html" target="blank">${ _("Learn more about Indico and Security") }</a></div>
    </div>
</div>

<li id="protectionBar" class="protectionBar protectionBar${protection[0]}">
    <img src=${ shieldIconURL} border="0" style="float:left; padding-right:5px">
    <a>${protection[1]}</a>
</li>


<script type="text/javascript">
$(".protectionBar").qtip({

    style: {
        width: '200px',
        classes: 'ui-tooltip-rounded ui-tooltip-shadow ui-tooltip-popup',
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
