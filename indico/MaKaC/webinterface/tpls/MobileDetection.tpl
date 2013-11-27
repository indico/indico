<%page args="conf=None"/>
<div class="mobile-device-header" style="display:none">
    <div class="text">${_("There is a Mobile version of Indico. Would you like to try it?")}</div>
    <div class="toolbar">
        <div class="group">
            <div id="useMobile" class="i-button accept">${_("Yes")}</div>
        </div>
        <div class="group">
            <div id="useFullVersion" class="i-button">${_("Not now")}</div>
        </div>
    </div>
</div>

 <script type="text/javascript">
     $("#useMobile").click(function(){
         var url = "${Config.getInstance().getMobileURL()}";
         % if conf :
             url += "/event/"+${conf.getId()};
             % if conf.hasAnyProtection():
                   url += "?pr=yes";
             % endif
         % endif
         window.location.href=url;
     });

     $("#useFullVersion").click(function(){
         $.jStorage.set("useIndicoDesktop", true, {TTL: 604800000}); //1 week TTL
         $(".mobile-device-header").hide();
     });

     $(function() {
        if($.mobileBrowser && !$.jStorage.get("useIndicoDesktop")){
            $(".mobile-device-header").show();
        }
     });
 </script>