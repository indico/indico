<table align="center" width="95%%">
    <tr>
        <td>
            <br>
            <table width="90%%" align="center">
                %(calendar)s
            </table>
        </td>
    </tr>
</table>

<form action="" method="GET">
    <input type=hidden name=daystring value="%(daystring)s">
    <input type=hidden name=monthstring value="%(monthstring)s">
    <input type=hidden name=yearstring value="%(yearstring)s">
    <input type=hidden name=month value="%(month)s">
    <input type=hidden name=year value="%(year)s">
    <input type=hidden name=date value="%(date)s">
    <input type="hidden" name="form" value="%(form)s">
</form>

<script type="text/javascript">

function SetDate(d,m,y)
{
  window.opener.document.forms[%(form)s].%(daystring)s.value = d;
  window.opener.document.forms[%(form)s].%(daystring)s.onchange();
  window.opener.document.forms[%(form)s].%(monthstring)s.value = m;
  window.opener.document.forms[%(form)s].%(monthstring)s.onchange();
  window.opener.document.forms[%(form)s].%(yearstring)s.value = y;
  window.opener.document.forms[%(form)s].%(yearstring)s.onchange();
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