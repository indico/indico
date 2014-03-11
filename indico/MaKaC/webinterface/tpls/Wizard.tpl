<% from indico.util.i18n import getLocaleDisplayNames %>
<form id="wizard-form" action="" method="POST">
  <center>
    <table width="80%">
      <tbody>
        <tr>
          <td colspan="3" align="center">
            <h2 class="page_title">${ _("Admin Creation Wizard")}</h2>
          </td>
        </tr>
        <tr>
          <td colspan="3" height="80em"></td>
        </tr>

        <tr class="stepTitle1">
          <td colspan="3">
            <b>${ _("1. User creation")}</b>
          </td>
        </tr>
        <tr>
          <td colspan="3" bgcolor="black"></td>
        </tr>
        <tr>
          <td align="right">
            <font color="gray"> ${ _("First name")}</font>
          </td>
          <td align="left" width="100%">
            <input id="name" type="text" name="name" value=${ name } required>
          </td>
        </tr>
        <tr>
          <td align="right">
            <font color="gray"> ${ _("Family name")}</font>
          </td>
          <td align="left">
            <input id="surName" type="text" name="surName" value=${ surName } required>
          </td>
        </tr>
        <tr>
          <td align="right">
            <font color="gray"> ${ _("Email")}</font>
          </td>
          <td align="left">
            <input id="userEmail" type="email" name="userEmail" value=${ userEmail } required>
          </td>
        </tr>
        <tr>
          <td align="right">
            <font color="gray"> ${ _("Login")}</font>
          </td>
          <td align="left">
            <input id="login" type="text" name="login" value=${ login } required>
          </td>
        </tr>
        <tr>
          <td align="right">
            <font color="gray"> ${ _("Password")}</font>
          </td>
          <td align="left">
            <input id="password" type="password" name="password" value="" required>
          </td>
        </tr>
        <tr>
          <td align="right" nowrap>
            <font color="gray"> ${ _("Password (again)")}</font>
          </td>
          <td align="left">
            <input id="passwordBis" type="password" name="passwordBis" value="" required pattern="">
          </td>
        </tr>
        <tr>
          <td colspan="3" height="20em"></td>
        </tr>
        <tr>
          <td colspan="3" align="center">
            <a id="nextStep1" class="i-button icon-expand" title="Next step"></a>
          </td>
        </tr>

        <tr class="stepTitle2">
          <td colspan="3">
            <b>${ _("2. Server Settings")}</b>
          </td>
        </tr>
        <tr>
          <td colspan="3" bgcolor="black"></td>
        </tr>
        <tr>
          <td align="right">
            <font color="gray">${ _("Language")}</font>
          </td>
          <td bgcolor="white" width="100%" align="left">
            <select size=1 name="lang">
                <script type='text/javascript'>
                  var lang = navigator.language || navigator.userLanguage;
                  var selected;
                  % for l in getLocaleDisplayNames():
                    selected = '';
                    if ('${l[0]}'.split('_')[0] == lang.split('-')[0])
                      selected = ' selected';
                    document.write('<option value="${l[0]}"'+selected+'>${l[1]}</option>');
                  % endfor
                </script>
            </select>
          </td>
          <td align="right" style="vertical-align:top;">
            <a id="previousStep2" class="i-button icon-collapse" title="Previous step"></a>
          </td>
        </tr>
        <tr>
          <td align="right">
            <font color="gray">${ _("Timezone")}</font>
          </td>
          <td bgcolor="white" width="100%" align="left">
            <select name="timezone">${ timezoneOptions }</select>
          </td>
        </tr>
        <tr>
          <td align="right">
            <font color="gray"> ${ _("Organisation")}</font>
          </td>
          <td align="left">
            <input id="organisation" type="text" name="organisation" value=${organisation} required>
          </td>
        </tr>
        <tr>
          <td colspan="3" height="20em">
        </tr>
        <tr>
          <td colspan="3" align="center">
            <a id="nextStep2" class="i-button icon-expand" title="Next step"></a>
          </td>
        </tr>

        <tr class="stepTitle3">
          <td colspan="3">
            <b>${ _("3. Instance tracking")}</b>
          </td>
        </tr>
        <tr>
          <td colspan="3" bgcolor="black"></td>
        </tr>
        <tr>
          <td colspan="2" align="left">
            <table width="50%">
              <tr>
                <td>
                  <font color="gray">
                    ${_("By accepting the Instance Tracking Terms you accept:")}
                    <ul>
                      <li>${ _("sending anonymous statistic data to Indico@CERN;")}</li>
                      <li>${ _("receiving security warnings from the Indico team;")}</li>
                      <li>${ _("receiving a notification when a new version is released.")}</li>
                    </ul>
                    ${_("Please note that no private information will ever be sent to Indico@CERN and that you will be able to change the Instance Tracking settings anytime in the future (from Server Admin, General Settings).")}
                  </font>
                </td>
              </tr>
            </table>
          </td>
          <td align="right" style="vertical-align:top;">
            <a id="previousStep3" class="i-button icon-collapse" title="Previous step"></a>
          </td>
        </tr>
        <tr>
          <td align="right">
            <font color="gray"> ${ _("Accept")}</font>
          </td>
          <td align="left" width="100%">
            <input id="accept" type="checkbox" name="accept" value="${ _("checked")}" ${checked}>
          </td>
        </tr>
        <tr>
          <td align="right">
            <font color="gray"> ${ _("Email")}</font>
          </td>
          <td align="left">
            <input id="itEmail" type="text" name="instanceTrackingEmail" value=${instanceTrackingEmail}>
          </td>
        </tr>
        <tr>
          <td colspan="3" height="20em"></td>
        </tr>
        <tr>
          <td colspan="3" align="center">
            <a href="#" id="submit-wizard" class="i-button icon-checkmark" title="Confirm"></a>
          </td>
        </tr>

      </tbody>
    </table>
  </center>
</form>

<style type="text/css">

  input:focus:invalid, input:invalid {
    border: 1px solid red;
  }

  input:focus:valid, input:valid {
    border: 1px solid green;
  }

</style>

<script type='text/javascript'>

  function toggleSection(section){
    $('tr.stepTitle'+section).next().nextUntil('tr.stepTitle'+(section+1)).toggle();
  }

  function expandCollapse(first, second){
    toggleSection(first);
    toggleSection(second);
  }

  function nextStep(current){
    expandCollapse(current, current+1);
  }

  function previousStep(current){
    expandCollapse(current, current-1);
  }

  $('#nextStep1').on('click', function(e){
    var name = document.getElementById('name');
    var surName = document.getElementById('surName');
    var userEmail = document.getElementById('userEmail');
    var login = document.getElementById('login');
    var password = document.getElementById('password');
    var passwordBis = document.getElementById('passwordBis');

    var msg = "";
    if (name.validity.valueMissing){
      msg = "${ _("You must enter a name.")}"+"\n";
    }
    if (surName.validity.valueMissing){
      msg = msg+"${ _("You must enter a surname.")}"+"\n";
    }
    if (userEmail.validity.valueMissing){
      msg = msg+"${ _("You must enter an user email address.")}"+"\n";
    }
    else if (!userEmail.validity.valid){
      msg = msg+"${ _("You must enter a valid user email address.")}"+"\n";
    }
    if (login.validity.valueMissing){
      msg = msg+"${ _("You must enter a login.")}"+"\n";
    }
    if (password.validity.valueMissing){
      msg = msg+"${ _("You must define a password.")}"+"\n";
    }
    if (password.value != passwordBis.value){
      msg = msg+"${ _("You must enter the same password twice.")}";
    }

    if (msg != "")
      alert(msg);
    else
      nextStep(1);
  });

  $('#nextStep2').on('click', function(e){
    var organisation = document.getElementById('organisation');

    var msg = "";
    if (organisation.validity.valueMissing){
      msg = "${ _("You must enter the name of your organisation.")}";
    }

    if (msg != "")
      alert(msg);
    else
      nextStep(2);
  });

  $('#previousStep2').on('click', function(e){
    previousStep(2);
  });

  $('#previousStep3').on('click', function(e){
    previousStep(3);
  });

  $('#accept').on('change', function(e){
    var accept = document.getElementById('accept');
    var itEmail = document.getElementById('itEmail');

    if (accept.checked)
      itEmail.required = true;
    else
      itEmail.required = false;
  });

  $('#password').on('input', function(e){
    var password = document.getElementById('password');
    var passwordBis = document.getElementById('passwordBis');

    passwordBis.pattern = password.value;
  });

  $('#submit-wizard').on('click', function(e){
    var itEmail = document.getElementById('itEmail');

    var msg = "";
    if (itEmail.validity.valueMissing){
      msg = "${ _("You must enter an email address for Instance Tracking.")}";
    }
    else if (itEmail.validity.valid){
      msg = "${ _("You must enter an email address for Instance Tracking.")}";
    }

    if (msg != "")
      alert(msg);
    else {
      e.preventDefault();
      $('#wizard-form').submit();
    }
  });

  toggleSection(2);
  toggleSection(3);
</script>
