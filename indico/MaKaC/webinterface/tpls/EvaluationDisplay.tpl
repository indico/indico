
      <center>
      <% questions = evaluation.getQuestions() %>
      <% if questions==None or len(questions)<=0: %>
        <br/>
        <br/>
        <font color="#E25300">
          <b> <%= _("This evaluation form is not ready")%>:</b>  <%= _("It has no question.")%><br/><br/>
           <%= _("Please advise the surveyor")%><% if evaluation.getContactInfo().strip()!="": %> : <%=evaluation.getContactInfo()%><% end %>.
        </font>
        <br/>
        <br/>
        <br/>
        <br/>
      <% end %>
      <% if questions!=None and len(questions)>0: includeTpl('EvaluationShow') %>
      <% end %>
      </center>
