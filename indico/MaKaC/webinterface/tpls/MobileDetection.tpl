<div class="mobile-device-header" style="display:none">
    <div class="text">${_("There is a Mobile version of Indico. Would you like to try it?")}</div>
    <div class="i-buttons">
        <div id="useMobile" class="i-button accept">${_("Yes")}</div>
        <div id="useFullVersion" class="i-button">${_("Not now")}</div>
    </div>
</div>

 <script type="text/javascript">
     $("#useMobile").click(function(){
         var url = "${Config.getInstance().getMobileURL()}";
         var confId = $.urlParam("confId");
         if(confId){
             url += "/event/"+confId;
         }
         window.location.replace(url);
     });

     $("#useFullVersion").click(function(){
         $.jStorage.set("useIndicoDesktop", true, {TTL: 604800000}); //1 week TTL
         $(".mobile-device-header").hide();
     });
     if(isMobile() && !$.jStorage.get("useIndicoDesktop")){
         $(".mobile-device-header").show();
     }
 </script>