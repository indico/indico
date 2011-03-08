
<% questions = evaluation.getQuestions() %>
% if questions==None or len(questions)<=0:
    <br/>
    <br/>
    <span style="color:#E25300; margin-bottom: 50px;">
      % if evaluation.isVisible():
       ${ _("Nothing to preview: create your evaluation in the Edit section.")}
      % endif
      % if not evaluation.isVisible():
      ${ _("Nothing to preview: first enable the evaluation in the Setup section.")}
      % endif
    </span>
% endif

% if questions!=None and len(questions)>0:
    <br/>
    <span style="color:#E25300;">${ _("Note: Feel free to play with this form, submitted information won't be recorded.")}</span>
    <br/><br/><br/>

    <%include file="EvaluationShow.tpl"/>
% endif
