$(document).ready(function() {
  /**
   * The DOM structure of the Poster & Badge designing pages is
   * nearly identical, albeit with slight difference. This JavaScript
   * affects both, permitting the PDF Options dialog and enforcing
   * that a radio button must be selected for the download PDF button
   * to function.
   */

  $('#badgePDFOptions').dialog({
    modal: true,
    resizable: false,
    autoOpen: false,
    maxHeight: '90%',
    buttons: {
      Ok: function() {
        $(this).dialog('close');
      }
    }
  });

  $('#showPDFLayout').click(function() {
    $('#badgePDFOptions').dialog('open');
    return false;
  });

  $('#downloadPDF').click(function() {
    var data = $('#create_form #config_data');
    // set data directly in form
    data.html('');
    data.append($('#badgePDFOptions input').clone());
    $('#create_form').submit();
    return false;
  });

  var get_radio_buttons = function() {
    return $(document).find('[name=templateId]');
  };
  var has_template_selected = function() {
    var buttons = get_radio_buttons();
    var has_checked = false;

    buttons.map(function() {
      if ($(this).prop('checked')) {
        has_checked = true;
      }
    });

    return has_checked;
  };

  var ascertain_dl_button_status = function() {
    $('#downloadPDF').prop('disabled', !has_template_selected());
  };

  $('input[name=templateId]:radio').change(function() {
    ascertain_dl_button_status();
  });

  ascertain_dl_button_status();

});