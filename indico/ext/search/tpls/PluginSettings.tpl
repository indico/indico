<table>
    <tr>

    <td>${ _("Default search engine")}</td>
    <td><div id="defaultSearch"></div></td>

</table>
<script type="text/javascript">

    var checkState = function() {
        var _checkState = function(state){
            if (state == SourceState.Error) {
                IndicoUtil.errorReport($T("Error saving"));
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
    var languageSelector = new SelectRemoteWidget("search.getSEAList",{},langCallback);
</script>