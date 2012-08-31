    <form name="EvalEditQuestion" action="${actionUrl}" method="post" onsubmit="return controle()">
      <!--general information start-->
      <table class="evalEditMain">
        <!--input Required-->
        <tr>
          <td class="titleCellTD"><span class="titleCellFormat">${ _("Required")}</span></td>
          <td id="requiredCell" class="inputCelTD">
            <input type="checkbox" name="required" ${required}/>
          </td>
        </tr>
        <!--input Question-->
        <tr>
          <td class="titleCellTD"><span class="titleCellFormat">* ${ _("Question")}</span></td>
          <td class="inputCelTD"><input type="text" class="textType" name="questionValue" value="${questionValue}"/></td>
        </tr>
        <!--input Keyword-->
        <tr>
          <td class="titleCellTD"><span class="titleCellFormat">*${ _("Keyword")}</span></td>
          <td id="keywordCell" class="inputCelTD">
            <input class="shortInput" type="text" name="keyword" maxlength="25" value="${keyword}"/>
          </td>
        </tr>
        <!--input Description of question-->
        <tr>
          <td class="titleCellTD"><span class="titleCellFormat">${ _("Description")}</span></td>
          <td class="inputCelTD"><textarea name="description" rows="5" cols="50" >${description}</textarea></td>
        </tr>
        <!--input Help-->
        <tr>
          <td class="titleCellTD"><span class="titleCellFormat"> ${ _("Help")}</span></td>
          <td class="inputCelTD"><input type="text" class="textType" name="help" value="${help}"/></td>
        </tr>
        <!--input Default answer-->
        ${defaultAnswer}
        <!--input Postion-->
        <tr>
          <td class="titleCellTD"><span class="titleCellFormat"> ${ _("Position in form")}</span></td>
          <td class="inputCelTD">
            ${position}
          </td>
        </tr>
      </table>
      <!--general information end-->

      <!--ChoicesItems-->
      % if choiceItems.strip()!="" :
        <table class="evalEditMain">
          <tr>
            <td class="titleCellTD">
              <span class="titleCellFormat" id="choiceItemsCell">
                *Choice Items
              </span>
            </td>
            <td class="inputCelTD">
            ${choiceItems}
            </td>
          </tr>
        </table>
      % endif


      <!--submission-->
      <table class="evalEditMain">
        <!--submit save question-->
        <tr>
          <td class="submitCelTD">
            <input class="btn" type="submit" name="save" value="${saveButtonText}" onfocus="saveIsFocused=true;" onblur="saveIsFocused=false;"/>
            <input class="btn" type="submit" name="cancel" value="${ _("cancel")}"/>
          </td>
        </tr>
      </table>
    </form>

    <!--data checking-->
    <script type="text/javascript">
      var saveIsFocused = false;
      var questionValue = document.EvalEditQuestion.questionValue;
      var keyword = document.EvalEditQuestion.keyword;
      var choiceItem_1 = document.EvalEditQuestion.choiceItem_1;
      var choiceItem_2 = document.EvalEditQuestion.choiceItem_2;
      // we must enter a question and a questionID.
      // we must enter choiceItems (in case of Radio buttons, Checkboxes, ...).
      function controle(){
        if (saveIsFocused && questionValue != null && questionValue.value == ""){
          new AlertPopup($T("Warning"), $T("Please enter a Question.")).open();
          return false;
        }
        else if (saveIsFocused && keyword != null && keyword.value == ""){
          new AlertPopup($T("Warning"), $T("Please enter a Keyword.")).open();
          return false;
        }
        else if (saveIsFocused && choiceItem_1 != null && choiceItem_1.value == ""){
          new AlertPopup($T("Warning"), $T("Please enter all value for Choice Items.")).open();
          return false;
        }
        else if (saveIsFocused && choiceItem_2 != null && choiceItem_2.value == ""){
          new AlertPopup($T("Warning"), $T("Please enter all values for Choice Items.")).open();
          return false;
        }
        else if (saveIsFocused && choiceItem_1 != null && choiceItem_2 != null && choiceItem_1.value == choiceItem_2.value){
          new AlertPopup($T("Warning"), $T("Please enter different values for Choice Items.")).open();
          return false;
        }
        else{
          return true;
        }
      }
      // for choiceItems (e.g. in case of Radio buttons, Checkboxes, ...)
      function addField(current) {
        var prev = current - 1;
        var next = current + 1;
        document.getElementById("field_"+current).innerHTML =
          "<input type='${javascriptChoiceItemsType}' name='selectedChoiceItems' value='"+current+"'><input class='choiceItemText' type='text' name='choiceItem_"+current+"'>\n" +
          "<div id='field_"+next+"'><a href='javascript:addField("+next+")' style='padding-left:40px;'>${javascriptChoiceItemsAddImg}</a>\n<a href='javascript:removeField("+current+")'>${javascriptChoiceItemsRemoveImg}</a>\n</div>\n";
      }
      function removeField(current) {
        var prev = current - 1;
        var next = current + 1;
        if (current > ${choiceItemsNb})
          document.getElementById("field_"+current).innerHTML =
            "<a href='javascript:addField("+current+")' style='padding-left:40px;'>${javascriptChoiceItemsAddImg}</a>\n<a href='javascript:removeField("+prev+")'>${javascriptChoiceItemsRemoveImg}</a>\n</span>\n";
      }
    </script>
