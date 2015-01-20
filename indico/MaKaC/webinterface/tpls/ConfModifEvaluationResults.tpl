<% colors=["blue","green","yellow","pink"]; color=0 %>
<!-- EvaluationResults start -->
<form action="${actionUrl}" method="POST">
    <fieldset class="evalationResultsFieldset">
      <legend> ${ _("Options")}</legend>
      <b> ${ _("Submitters")}</b><br/>
      <ul>
        <li><input class="btn" type="submit" name="${selectSubmitters}" value="${selectSubmitters}" style="width:100px"/>
          <span class="contextHelp" title="${submittersContext}">
            ${ _("Currently selected")}: <small>${submittersVisible}</small>
          </span>
        </li>
        <!--<li><input class="btn" type="submit" name="export" value="${ _("export")}" style="width:100px"/></li>
        <li><input class="btn" type="submit" name="print" value="${ _("print")}" style="width:100px"/></li>-->
        <li><input class="btn" type="submit" name="${removeSubmitters}" value="${removeSubmitters}" style="width:100px"/></li>
      </ul>
      <b> ${ _("Statistics")}</b><br/>
      <ul>
        <li><input class="btn" type="submit" name="exportStats" value="${ _("export")}" style="width:100px"/></li>
        <!--<li>print</li>-->
      </ul>
    </fieldset>

    <fieldset class="evalationResultsFieldset" style="margin-top: 20px;">
      <legend>${ _("Statistics")}</legend>

      % if not evaluation.getNbOfSubmissions():
        <span style="color:#E25300">${ _("No submission yet...")}</span>
      % elif not selectedSubmissions and selectedSubmissions is not None:
        <span style="color:#E25300">${ _("No submitters selected...")}</span>
      % else:
        % for q in evaluation.getQuestions():
        <!--stat of question : start-->
          ${'<font color="red">*</font>' if q.isRequired() else ""}
          <b>${ "%s. %s"%(q.getPosition(), q.getQuestionValue()) }</b>
          ${inlineContextHelp(_("Participation for this question = %s/%s")%(q.getNbOfFilledAnswers(selectedSubmissions),q.getNbOfAnswers(selectedSubmissions)))}
          % if isinstance(q, Box):
            <ul>
              % for a in q.getAnswers(selectedSubmissions):
                ${"<li>"+a.getAnswerValue()+"</li>" if a.getAnswerValue()!="" else ""}
              % endfor
            </ul>
          % endif
          % if isinstance(q, Choice):
<% choiceItemsNb=q.getNbOfChoiceItems() %>
            <p>
              % if choiceItemsNb<2:
                <i> ${ _("[Warning] it's strange: you have less than 2 choice items for this kind of question...")}</i>
              % endif

              % if choiceItemsNb==2 and q.areAllAnswersFilled(selectedSubmissions):
<% choiceItem1=q.getChoiceItemsKeyAt(1); choiceItem2=q.getChoiceItemsKeyAt(2); %>
              <!--inline graphic : start-->
              <table class="statsGraphContainer">
                <tr>
                  <td class="statsGraphHead"/>
                  <td>
                    <table class="statsHead">
                      <tr>
                        <td>
                          ${choiceItem1}
                          (${q.getPercentageAnswersLike(choiceItem1,selectedSubmissions)}&#37;)
                        </td>
                        <td align="right">
                          ${choiceItem2}
                          (${q.getPercentageAnswersLike(choiceItem2,selectedSubmissions)}&#37;)
                        </td>
                      </tr>
                    </table>
                    <table class="statsGraph">
                      <tr>
                        <td class="yellow" width="${q.getPercentageAnswersLike(choiceItem1,selectedSubmissions)}%" />
                        <td class="green" width="${q.getPercentageAnswersLike(choiceItem2,selectedSubmissions)}%" />
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>
              <!--inline graphic : end-->
              % endif

              % if choiceItemsNb>2 or ( choiceItemsNb==2 and not q.areAllAnswersFilled(selectedSubmissions) ):
<% color=0 %>
              <!--multilines graphic : start-->
              <table class="statsGraphContainer">
                % for choiceItem in q.getChoiceItemsOrderedKeys():
<% percent=q.getPercentageAnswersLike(choiceItem,selectedSubmissions) %>
                  <tr>
                    <td class="statsGraphHead">${choiceItem}</td>
                    <td>
                      <table class="statsGraph">
                        <tr>
                          % if percent>=10:
                            <td class="${ colors[color%len(colors)]}<% color+=1 %>" width="${percent}%" align="right">${percent}&#37;</td>
                            <td width="${100-percent}%"/>
                          % endif
                          % if percent<10:
                            <td class="${ colors[color%len(colors)]}<% color+=1 %>" width="${percent}%" />
                            <td width="${100-percent}%">&nbsp;${percent}&#37;</td>
                          % endif
                        </tr>
                      </table>
                    </td>
                  </tr>
                % endfor
              </table>
              <!--multilines graphic : end-->
              % endif
            </p>
          % endif
          <br/>
        <!--stat of question : end-->
        % endfor
      % endif
    </fieldset>
</form>
<!-- EvaluationResults end -->
