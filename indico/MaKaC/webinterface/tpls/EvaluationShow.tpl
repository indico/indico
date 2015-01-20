<% questions = evaluation.getQuestions() %>
        <!--EvaluationShow start-->
        <form name="EvaluationShow" action="${actionUrl}" method="POST" onsubmit="return check()">
          <table class="evalEditPreviewTitle">
            <tr>
              <td class="title" colspan="2">${evaluation.getTitle()}</td>
            </tr>
            <tr>
              <td align="left">
                % if evaluation.isAnonymous() :
                   ${ _("Note: This survey is anonymous.")}
                % endif
                % if not evaluation.isAnonymous() and user!=None :
                   ${ _("You will submit this form as")} "${user.getFullName()}".
                % endif
              </td>
              <td align="right">${ _("""Fields marked with <span style="color: red">*</span> are mandatory.""")}</td>
            </tr>
          </table>

          <table class="evalEditPreview">
            <% i=0 %>
            % for q in questions:
<% i+=1 %>
              <!--question start-->
              <tr ${'class="evalEditPreviewTrGrey"' if i%2==1 else ""}>
                <td class="displayField">
                  ${'<span style="color: red">*</span>' if q.isRequired() else ""}
                  ${ "%s. %s"%(q.getPosition(), q.getQuestionValue()) }
                  % if len(q.getHelp())>0:
                    ${inlineContextHelp(q.getHelp())}
                  % endif
                </td>
                <td class="inputCelTD" rowspan="2">
                  <% questionId = "q%s"%q.getPosition() %>
                  <span style="color: black" id="${questionId}">
                    % if not hasSubmittedEvaluation :
                      ${q.displayHtml(name=questionId,onblur="clearErrorMark(this);")}
                    % endif
                    % if hasSubmittedEvaluation :
                      ${q.displayHtmlWithUserAnswer(user,name=questionId,onblur="clearErrorMark(this);")}
                    % endif
                  </span>
                </td>
              </tr>
              <tr ${'class="evalEditPreviewTrGrey"' if i%2==1 else ""}>
                <td class="commentCelTD">${q.getDescription()}</td>
              </tr>
              <!--question end-->
            % endfor
          </table>

          <!--<input class="btn" type="submit" name="submit" value="${ _("submit")}" onclick="return check();"/>-->
          <!--<input class="btn" type="submit" name="cancel" value="${ _("cancel")}"/>-->
          <div style="margin: 20px;">
              <input class="btn" type="submit" name="submit" value="${ _("submit")}" onclick="submitIsClicked(true);"/>
              <input class="btn" type="submit" name="cancel" value="${ _("cancel")}" onclick="submitIsClicked(false);"/>
          </div>
        </form>
        <!--EvaluationShow end-->

        <!--data checking start-->
        <script type="text/javascript">
          <!--to know which submit button ("submit"/"cancel") has been pressed.-->
          var isSubmitClicked = false;
          function submitIsClicked(val){ isSubmitClicked = val; }
          <!--main check fct: return true if everything ok, false otherwise.-->
          function check(){
            if (isSubmitClicked){
              var success = true;
              % for q in questions:
% if q.isRequired():
                if (checkQuestion(document.EvaluationShow.q${q.getPosition()}, success)==false) success = false;
              % endif
% endfor
              if (success){
                return true;
              }
              else {
                new AlertPopup($T("Warning"), $T("Please fill in all required fields.")).open();
                return false;
              }
            }
            else return true;
          }
          <!--return true if current question is ok, false otherwise.-->
          function checkQuestion(question, success){
            if (question != null){
              <!--select input-->
              if (question.options){
                if (question.options[question.selectedIndex].text!=''){
                  question.style.background="white";
                }
                else {
                  question.style.background="#fbb";
                  success = false;
                }
              }
              <!--check input (radio+checkbox)-->
              else if (question.length){
                var checkFontText = document.getElementById(question[0].name);
                if (isChecked(question)){
                  checkFontText.style.color="black";
                }
                else{
                  checkFontText.style.color="red";
                  success = false;
                }
              }
              <!--standard input-->
              else {
                if (question.value != ""){
                  question.style.background="white";
                }
                else{
                  question.style.background="#fbb";
                  success = false;
                }
              }
            }
            return success;
          }
          <!--When user fills in information, error marks are removed if correct.-->
          function clearErrorMark(question){
            <!--recuperate the real question object, needed for checkboxes/radioButtons.-->
            question = eval("document.EvaluationShow." + question.name);
            <!--select input-->
            if (question.options){
              if (question.options[question.options.selectedIndex].text!='')  question.style.background='white';
            }
            <!--check input (radio+checkbox)-->
            else if (question.length){
              if (isChecked(question))
                document.getElementById(question[0].name).style.color="black";
            }
            <!--standard input-->
            else {
              if (question.value!='') question.style.background='white';
            }
          }
          <!--Returns a boolean indicating if one of the checkboxes/radioButtons are checked.-->
          function isChecked(question){
            for(var i=0; i<question.length; i++){
              if (question[i].checked){
                return true;
              }
            }
            return false;
          }
        </script>
        <!--data checking end-->
