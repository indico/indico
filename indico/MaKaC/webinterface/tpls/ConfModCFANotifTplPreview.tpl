<br>
<table width="80%" align="center" style="border-top:1px solid #777777; border-left:1px solid #777777">
    <% if conf.getAbstractMgr().getAbstractList(): %>
        <tr>
            <td style="color: #5294CC;border-bottom:1px solid #5294CC"> <%= _("From")%>&nbsp;&nbsp;&nbsp;</td>
            <td style="color: black"><b><%= From %></b></span></td>
        </tr>
        <tr>
            <td style="color: #5294CC;border-bottom:1px solid #5294CC"> <%= _("To")%>&nbsp;&nbsp;&nbsp;</td>
            <td style="color: black"><b><%= to %></b></span></td>
        </tr>
        <tr>
            <td style="color: #5294CC;border-bottom:1px solid #5294CC"> <%= _("Cc")%>&nbsp;&nbsp;&nbsp;</td>
            <td style="color: black"><b><%= cc %></b></span></td>
        </tr>
        <tr>
            <td style="color: #5294CC;border-bottom:1px solid #5294CC"> <%= _("Subject")%>&nbsp;&nbsp;&nbsp;</td>
            <td style="color: black"><b><%= subject %></b></span></td>
        </tr>
        <tr>
            <td style="color: #5294CC;border-bottom:1px solid #5294CC"> <%= _("Body")%>&nbsp;&nbsp;&nbsp;</td>
            <td width="100%" style="color:black"><pre><%= body %></pre></td>
        </tr>
    <% end %>
    <% else: %>
        <tr>
            <td style="color: #5294CC;border-bottom:1px solid #5294CC"> <%= _("From")%>&nbsp;&nbsp;&nbsp;</td>
            <td style="color: black"><b><%= _("No preview available") %></b></span></td>
        </tr>
        <tr>
            <td style="color: #5294CC;border-bottom:1px solid #5294CC"> <%= _("To")%>&nbsp;&nbsp;&nbsp;</td>
            <td style="color: black"><b><%= _("No preview available") %></b></span></td>
        </tr>
        <tr>
            <td style="color: #5294CC;border-bottom:1px solid #5294CC"> <%= _("Cc")%>&nbsp;&nbsp;&nbsp;</td>
            <td style="color: black"><b><%= _("No preview available") %></b></span></td>
        </tr>
        <tr>
            <td style="color: #5294CC;border-bottom:1px solid #5294CC"> <%= _("Subject")%>&nbsp;&nbsp;&nbsp;</td>
            <td style="color: black"><b><%= _("No preview available") %></b></span></td>
        </tr>
        <tr>
            <td style="color: #5294CC;border-bottom:1px solid #5294CC"> <%= _("Body")%>&nbsp;&nbsp;&nbsp;</td>
            <td width="100%" style="color:black"><%= _("An abstract must be submitted to display the preview") %></td>
        </tr>
    <% end %>
</table>
<br>
