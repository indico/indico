<% import MaKaC.webinterface.urlHandlers as urlHandlers %>

<table class="Revtab" width="90%%" cellspacing="0" align="center" border="0" style="border-left: 1px solid #777777;padding-left:2px">
    <tr>
        <td nowrap class="groupTitle" colspan=5>
            <%= _("User competences")%>
            <span id="competencesHelp"></span> 
        </td>
    </tr>
    <tr>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">Id</td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">Name</td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"><%= _("Responsabilities")%></td>
        <td colspan=2 nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"><%= _("Competences")%></td>
    </tr>
   
    
    <% for user, competences in ConfReview.getAllUserCompetences(): %>
        <tr valign="top">
            <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;"><%= user.getId() %></td>
            <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;"><%= user.getFullName()%></td>
            <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                <%= ", ".join(ConfReview.getUserReviewingRoles(user)) %>
            </td>
            <td>
                <span id="competences_<%= user.getId() %>"></span>
            </td>
        </tr>
    <% end %>
</table>

<script type="text/javascript">

var keyWordfieldList = new Array()
<% for user, competences in ConfReview.getAllUserCompetences(): %>

    new IndicoUI.Widgets.Generic.keywordField(
        $E('competences_<%= user.getId() %>'),
        'oneLineListItem',
        'reviewing.conference.changeCompetences',
        {
            conference: '<%= Conference.getId() %>',
            user: '<%= user.getId() %>'
        }
    );
    
<% end %>
</script>