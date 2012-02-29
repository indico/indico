<table class="groupTable">
<tr>
  <td colspan="2"><div class="groupTitle">${ _("Domain control ")}</div></td>
</tr>
</table>
<div>${ locator }</div>
<div class="domainEnable"></div>
<div><ul style='list-style-type:none;'>${domains}</ul></div>
<script type="text/javascript">
IndicoUI.executeOnLoad(function(){
    if ($(':checkbox:checked').length==0){
        $('.domainEnable').html(${_('<B style="color:#B02B2C;">Domain control is disabled.</B><br>To enable it, choose at least one of the domains below:')|n,j});
    }
    else{
        $('.domainEnable').html(${_('<B style="color:#128F33;">Domain control is enabled.</B>')|n,j});
    }
});
var checkId = null;
$(':checkbox:not(:checked)').live('change', function(){
    checkId = $(this).val();
    indicoRequest('event.protection.toggleDomains', {
        confId: ${conference.getId()},
        domainId: $(this).val(),
        add: false
    },
    function(result, error) {
        var domain = '#domain'+checkId;
        if ($(':checkbox:checked').length==0){
            $('.domainEnable').html(${_('<B style="color:#B02B2C;">Domain control is disabled.</B><br>To enable it, choose at least one of the domains below:')|n,j});
        }
        $(domain).attr('style','margin-left:10px; color:#128F33;');
        $(domain).text("saved");
        setTimeout(function(){
            $(domain).text("");
        }, 1000);
        if(error) {
            IndicoUtil.errorReport(error);
        } else{
            (new AlertPopup($T('Domain removed'))).open();
        }
    });
});
$(':checkbox:checked').live('change', function(){
    checkId = $(this).val();
    indicoRequest('event.protection.toggleDomains', {
        confId: ${conference.getId()},
        domainId: $(this).val(),
        add: true
    },
    function(result, error) {
        var domain = '#domain'+checkId;
        if ($(':checkbox:checked').length!=0){
            $('.domainEnable').html(${_('<B style="color:#128F33;">Domain control is enabled.</B>')|n,j});
        }
        $(domain).attr('style','margin-left:10px; color:#128F33;');
        $(domain).text("saved");
        setTimeout(function(){
            $(domain).text("");
        }, 1000);
        if(error) {
            IndicoUtil.errorReport(error);
        } else{
            (new AlertPopup($T('Domain added'))).open();
        }
    });
});
</script>
