<div class="container" style="max-width: 700px;">
    <div class="groupTitle"><%= _("Indico contact information")%></div>
    
    
    <div class="indicoHelp">
        <% if supportEmail.strip(): %>
        <div class="title"><%= _("Helpdesk")%></div>
        
        <div class="content">
            <p><em><%= _("For support using indico at CERN please contact the indico helpdesk:")%></em></p>
            
            <div style="margin: 15px 50px;"><a href="ihelp/cm.html"><%= supportEmail %></a></div>
        </div>
        <% end %>
        <%if teamEmail.strip(): %>    
        <div class="title"><%= _("Development and Software support")%></div>
    
        <div class="content">
            <p><em><%= _("The developers team can assist you for installing the indico software and solving technical questions:")%></em></p>
            
            <div style="margin: 15px 50px;"><a href="ihelp/cm.html"><%= teamEmail %></a></div>
        </div>
        <% end %>
    </div>

</div>