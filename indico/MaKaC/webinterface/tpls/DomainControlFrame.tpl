<table class="groupTable">
<tr>
  <td colspan="2"><div class="groupTitle">${ _("Domain control ")}<span id="domainControl"></span></div></td>
</tr>
<tr>
  <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Allowed domains")}<br><font size="-2">(${ _("if no domain is selected<br>no control is applied")})</font></span></td>
  <td class="blacktext">
    ${ locator }
    <table width="auto">
        ${ domains }
    </table>
  </td>
</tr>
</table>
<script type="text/javascript">
IndicoUI.executeOnLoad(function(){
    if ($(':checkbox:checked').length==0){
        $('#domainControl').text(${ _("(disabled)")|n,j});
        $('#domainControl').attr('style','color: #B02B2C;');
    }
    else{
        $('#domainControl').text(${ _("(enabled)")|n,j});
        $('#domainControl').attr('style','color: #128F33;');
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
            $('#domainControl').text(${ _("(disabled)")|n,j});
            $('#domainControl').attr('style','color: #B02B2C;');
        }
        $(domain).attr('style','margin-left:10px; color:#B02B2C;');
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
            $('#domainControl').text(${ _("(enabled)")|n,j});
            $('#domainControl').attr('style','color: #128F33;');
        }
        $(domain).attr('style','margin-left:10px; color:#B02B2C;');
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
