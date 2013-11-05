% if announcement_header != '':
    <div class="pageOverHeader clearfix" id="announcementHeader">
        <div class="left">
        ${ announcement_header }
        </div>
        <div class="icon-close icon-announcement" id="closeAnnouncement"></div>
    </div>
    <script type="text/javascript">
    $('#closeAnnouncement').click(function(){
        $.jStorage.set("hideAnnouncement", "${ md5_announcement_header }");
        $('#announcementHeader').slideUp("fast");
    });

    $(function() {
        if($.jStorage.get("hideAnnouncement") != "${ md5_announcement_header }"){
            $("#announcementHeader").show();
        }
     });
    </script>
% endif
