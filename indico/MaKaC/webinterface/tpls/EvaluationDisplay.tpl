<%inherit file="ConfDisplayBodyBase.tpl"/>

<%block name="title">
    ${body_title}
</%block>

<%block name="content">
      <center>
          <% questions = evaluation.getQuestions() %>
          % if questions==None or len(questions)<=0:
            <br/>
            <br/>
            <font color="#E25300">
              <b> ${ _("This evaluation form is not ready")}:</b>  ${ _("It has no question.")}<br/><br/>
               ${ _("Please advise the surveyor")}${" : "+evaluation.getContactInfo() if evaluation.getContactInfo().strip()!="" else ""}.
            </font>
            <br/>
            <br/>
            <br/>
            <br/>
          % endif
          % if questions!=None and len(questions)>0:
            <%include file="EvaluationShow.tpl"/>
          % endif
      </center>
</%block>
