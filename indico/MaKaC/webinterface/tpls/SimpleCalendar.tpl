<table align="center" width="95%">
    <tr>
        <td>
            <br>
            <table width="90%" align="center">
                ${ calendar }
            </table>
        </td>
    </tr>
</table>

<form action="" method="GET">
    <input type=hidden name=daystring value="${ daystring }">
    <input type=hidden name=monthstring value="${ monthstring }">
    <input type=hidden name=yearstring value="${ yearstring }">
    <input type=hidden name=month value="${ month }">
    <input type=hidden name=year value="${ year }">
    <input type=hidden name=date value="${ date }">
    <input type="hidden" name="form" value="${ form }">
</form>

<script type="text/javascript">

function SetDate(d,m,y)
{
  window.opener.document.forms[${ form }].${ daystring }.value = d;
  window.opener.document.forms[${ form }].${ daystring }.onchange();
  window.opener.document.forms[${ form }].${ monthstring }.value = m;
  window.opener.document.forms[${ form }].${ monthstring }.onchange();
  window.opener.document.forms[${ form }].${ yearstring }.value = y;
  window.opener.document.forms[${ form }].${ yearstring }.onchange();
  window.close();
}

function PreviousMonth()
{
  if (document.forms[0].month.value == 1)
  {
    document.forms[0].month.value = 12;
    document.forms[0].year.value = parseInt(document.forms[0].year.value) - 1;
  }
  else
  {
    document.forms[0].month.value = parseInt(document.forms[0].month.value) - 1;
  }
  document.forms[0].submit();
}

function NextMonth()
{
  if (document.forms[0].month.value == 12)
  {
    document.forms[0].month.value = 1;
    document.forms[0].year.value = parseInt(document.forms[0].year.value) + 1;
  }
  else
  {
    document.forms[0].month.value = parseInt(document.forms[0].month.value) + 1;
  }
  document.forms[0].submit();
}

function PreviousYear()
{
  document.forms[0].year.value = parseInt(document.forms[0].year.value) - 1;
  document.forms[0].submit();
}

function NextYear()
{
  document.forms[0].year.value = parseInt(document.forms[0].year.value) + 1;
  document.forms[0].submit();
}


</script>
