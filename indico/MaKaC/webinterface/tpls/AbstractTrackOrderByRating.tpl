<table class="infoQuestionsTable" width="100%%" align="center" cellpadding="0" cellspacing="0" border="0">
    <tr>
        <td nowrap class="dataHeader" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #BBBBBB;"> <%= _("Question")%></td>
        <td nowrap class="dataHeader" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #BBBBBB;"> <%= _("Average<br>rating")%>
        <% inlineContextHelp(_('The rating is in a 0-100 scale.')) %> </td>
    </tr>
    <% for q,v in questions.iteritems():  %>
        <tr class="infoTR">
            <td nowrap class="content" style="padding-right:10px">&nbsp;<%= q %></td>
            <td nowrap class="content" style="padding-right:10px">&nbsp;<%= v %></td>
        </tr>
    <% end %>
</table>
<br>
<% if len(questions.keys()) == 0: %>
    <span style="padding-left: 10px;">There are no judgements with answered questions yet.</span>
<% end %>
<% if ratingAverage: %>
    <span>The abstract's average rating is: <b>%(ratingAverage)s</b></span>
<% end %>
