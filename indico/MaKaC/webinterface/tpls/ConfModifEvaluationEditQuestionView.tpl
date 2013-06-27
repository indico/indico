
        <!--view of question start-->
        <table class="evalEditViewContainer">
          <tr>
            <td>
              <table class="evalEditView">
                <tr>
                  <th class="greyGroupTitle">${keyword}${ inlineContextHelp(help) if len(help) > 0 else "" }</th>
                  <th>
                    <table class="evalEditViewActions">
                    <tr>
                      <td style="padding-right:10px;">
                        <form action="${actionUrl}" method="post">
                            <div>
                                  ${posChange}
                                  <noscript><div><input type="submit" value="${ _("move")}" class="btn" style="font-size:9px;"/></div></noscript>
                            </div>
                        </form>
                      </td>
                      <td style="padding-right:5px;">
                        <form action="${actionUrl}" method="post">
                            <div>
                                  ${editQuestion}
                            </div>
                        </form>
                      </td>
                      <td style="padding-right:2px;">
                        <form action="${removeQuestionUrl}" method="post">
                            <div>
                                  ${removeQuestionInput}
                            </div>
                        </form>
                      </td>
                    </tr>
                    </table>
                  </th>
                </tr>
                <tr>
                      <td class="displayField">
                        % if required:
                            <span style="color:red;">
                                ${required}
                            </span>
                        % endif
                    ${ "%s. %s"%(actualPosition, questionValue) }</td>
                  <td class="inputCelTD" rowspan="2">${input}</td>
                </tr>
                <tr>
                  <td class="commentCelTD">${description}</td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
        <!--view of question end-->
<script type="text/javascript">
$("[id^=questionRemove]").click(function(){
    var self = this;
    new ConfirmPopup($T("Remove question"),$T("Do you really want to remove this question?"), function(confirmed) {
        if(confirmed) {
            $(self).closest("form").submit();
        }
    }).open();
    return false;
});
</script>
