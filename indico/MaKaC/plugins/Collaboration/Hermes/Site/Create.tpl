<% from MaKaC.services.tools import toJsDate %>
<div class="hermesContainer">
<h3>Hermes videoconference</h3>
<div id="hermesBody">
    <img src="${ systemIcon("ui_loading") }" alt="Loading..." />
</div>
<script>
    var request = {
        conference: {
            id: "${ self_.conf.getId() }",
            title: "${ self_.conf.getTitle() }",
            start: ${ toJsDate(self_.conf.getStartDate()) },
            end: ${ toJsDate(self_.conf.getEndDate()) }
        },
        hermes: {
            action: "createConference"
        }
    };
    include(ScriptRoot + "indico/Hermes.js");
</script>
</div>
