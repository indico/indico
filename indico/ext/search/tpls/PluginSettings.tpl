<table>
    <tr>

    <td>${ _("Default search engine")}</td>
    <td><div id="defaultSearch"></div></td>
    <td><div id="status" style="color:green;display:none">${_("Saved!")}</div></td>
    </tr>

</table>
<script type="text/javascript">

    var checkState = function() {
        var _checkState = function(state){
            if (state == SourceState.Error) {
                IndicoUtil.errorReport($T("Error saving"));
            } else if(state == SourceState.Loaded) {
                $("#status").show();
                setTimeout(function(){$("#status").hide();}, 1000);
            }
        };
    return _checkState;
    };

    var langCallback = function(){
        $("#defaultSearch").html(languageSelector.draw().dom);
        languageSelector.observe(function(){
            var req = indicoSource('search.setDefaultSEA', {"agent":languageSelector.get()});
            req.state.observe(checkState());
        });
    };
    var languageSelector = new SelectRemoteWidget("search.getSEAList",{},langCallback, "searchAgent", $T("No search agents active"), ${defaultSearchEngine | n,j});
</script>