<br>
<table width="100%" align="center" cellpadding="0" cellspacing="0" border="0">
    <tr>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #BBBBBB;"> ${ _("Track")}</td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #BBBBBB;"> ${ _("Judgment")}</td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #BBBBBB;"> ${ _("Judged by")}</td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #BBBBBB;"> ${ _("Date")}</td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #BBBBBB;"> ${inlineContextHelp(_('The rating is in ' + str(scaleLower) + ' - ' + str(scaleHigher) + ' scale.'))}${ _("Average<br/>rating")}
 </td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #BBBBBB;"> ${ _("Comments")}</td>
    </tr>
    <tr><td>&nbsp;</td></tr>
    ${ tracks }
</table>
% if not judgements:
    <span style="padding-left: 10px;">There are no assessments yet.</span>
% endif
% if ratingAverage:
    <br>
    <span>The abstract's average rating is: <b>${ ratingAverage }</b></span>
% endif

<script>
function showQuestionDetails(questions, answers, average, total) {
    // Create the table and the headers
    var content = Html.div();
    var table = Html.table({className:'infoQuestionsTable', cellspacing:'0'});
    content.append(table);
    var tbody = Html.tbody();
    table.append(tbody);
    var trHeaders = Html.tr();
    tbody.append(trHeaders);
    var tdQuestion = Html.td({className:'dataHeader'},'Question');
    var tdValues = Html.td({className:'dataHeader'},'Value');
    trHeaders.append(tdQuestion);
    trHeaders.append(tdValues);

    // Create the table with the required data
    var tr;
    var tdQ; // the question
    var tdA; // the answer
    for (var i=0; i < questions.length ; i++) {
        tr = Html.tr({className: 'infoTR'});
        tdQ = Html.td({className: 'content'}, questions[i]);
        tdA = Html.td({className: 'content'}, answers[i]);
        tbody.append(tr);
        tr.append(tdQ);
        tr.append(tdA);
    }

    // Create the row with the total
    var trTotal = Html.tr();
    var tdTotal = Html.td();
    var tdTotalValue = Html.td();
    tdTotal = Html.td({className:'dataFooter'}, 'Total');
    tdTotalValue = Html.td({className:'dataFooter'}, total);
    tbody.append(trTotal);
    trTotal.append(tdTotal);
    trTotal.append(tdTotalValue);

    // Create the last row with the average
    var trFooter = Html.tr();
    var tdAverage = Html.td();
    var tdValue = Html.td();
    tdAverage = Html.td({className:'dataBold'}, 'Average');
    tdValue = Html.td({className:'dataBold'}, average);
    tbody.append(trFooter);
    trFooter.append(tdAverage);
    trFooter.append(tdValue);

    popup = new AlertPopup('Assessment details',content);
    popup.open();

}


</script>
