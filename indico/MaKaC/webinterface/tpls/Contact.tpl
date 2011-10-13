<div class="container" style="max-width: 700px;">
    <div class="groupTitle">${ _("Indico contact information")}</div>


    <div class="indicoHelp">
        % if supportEmail.strip():
        <div class="title">${ _("User support")}</div>

        <div class="content">
            <p><em>${ _("For support using indico at CERN please contact the indico helpdesk:")}</em></p>

            <div style="margin: 15px 50px;"><a href="mailto:${ supportEmail }">${ supportEmail }</a></div>
        </div>
        % endif
        %if teamEmail.strip():
        <div class="title">${ _("Development support and collaboration")}</div>

        <div class="content">
            <p><em>${ _("The developers team can assist you for installing the indico software and solving technical issues:")}</em></p>

            <div style="margin: 15px 50px;"><a href="mailto:${ teamEmail }">${ teamEmail }</a></div>
        </div>
        % endif
    </div>

</div>
