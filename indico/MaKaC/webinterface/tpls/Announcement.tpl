% if announcement_header:
    <div class="pageOverHeader clearfix" id="announcementHeader">
        <div class="left">
        ${announcement_header}
        </div>
        <div class="icon-close icon-announcement" id="closeAnnouncement"></div>
    </div>
    <script type="text/javascript">
    $('#closeAnnouncement').click(function(){
        $.jStorage.set("hideAnnouncement", "${announcement_header_hash}");
        $('#announcementHeader').slideUp("fast");
    });

    $(function() {
        if($.jStorage.get("hideAnnouncement") != "${announcement_header_hash}"){
            $("#announcementHeader").show();
        }
     });
    </script>
% endif
