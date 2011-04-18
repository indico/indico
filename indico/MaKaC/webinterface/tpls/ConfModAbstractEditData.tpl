<form action=${ postURL } method="POST" onsubmit="return pm.check();">
<tr><td>
    <table align="center" width="100%" border="0">
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Title")}</span>
            <span class="mandatoryField">*</span></td>
            <td><input type="text" id="abstractTitle" name="title" size="90" value=${ title }></td>
        </tr>
        ${ additionalFields }
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Primary authors")}</span></td>
            <td>
                <table cellspacing="0" cellpadding="0" width="50%" align="left" valign="middle" border="0">
                    ${ primaryAuthors }
                    <tr>
                        <td colspan="3">
                            <input type="submit" class="btn" name="remPrimAuthors" value="${ _("remove selected primary authors")}">
                            <input type="submit" class="btn" name="addPrimAuthor" value="${ _("new primary author")}">
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Co-authors")}</span></td>
            <td>
                <table cellspacing="0" cellpadding="0" width="50%" align="left" valign="middle" border="0">
                    ${ coAuthors }
                    <tr>
                        <td colspan="3">
                            <input type="submit" class="btn" name="remCoAuthors" value="${ _("remove selected co-authors")}">
                            <input type="submit" class="btn" name="addCoAuthor" value="${ _("new co-author")}">
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Contribution type")}</span></td>
            <td><select name="contribType">${ contribTypeItems }</select></td>
        </tr>
        <tr><td colspan="2">&nbsp;</td></tr>
        <tr align="center">
            <td colspan="2" style="border-bottom:1px solid #BBBBBB; padding-bottom: 5px;" valign="bottom" align="center">
                <input type="submit" class="btn" name="OK" value="${ _("submit")}">
                <input type="submit" class="btn" name="CANCEL" value="${ _("cancel")}" onclick="this.form.onsubmit= function(){return true;};">
            </td>
        </tr>
    </table>
</td></tr>
</form>
<script type="text/javascript">

var limitedFieldManagerList = [];
var limitedFieldList = ${ limitedFieldList };
var pm = new IndicoUtil.parameterManager();

pm.add($E('abstractTitle'), null, false);

function createLimitedFieldsMgr() {
    for (var i=0; i<limitedFieldList.length; i++) {
        var isMandatory = (limitedFieldList[i][4] == "True");
        if (limitedFieldList[i][3] == "words") {
            limitedFieldManagerList.push(new WordsManager($E(limitedFieldList[i][0]), limitedFieldList[i][1], $E(limitedFieldList[i][2]), isMandatory));
        } else {
            limitedFieldManagerList.push(new CharsManager($E(limitedFieldList[i][0]), limitedFieldList[i][1], $E(limitedFieldList[i][2]), isMandatory));
        }
    }
}

// On load
createLimitedFieldsMgr();

</script>
