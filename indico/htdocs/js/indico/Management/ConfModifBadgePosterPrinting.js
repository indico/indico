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
    appendTo: '#create_form',
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

    // TODO: remove ugly workaround when IE bug is solved
    // http://bugs.jquery.com/ticket/10550#comment:22
    $('#badgePDFOptions input[type=checkbox]:not(:checked)').addClass("_unchecked");
    var clone = $('#badgePDFOptions input').clone();
    _fixclonedcheckbox(clone);
    data.append(clone);

    $('#create_form').submit();
    return false;
  });

  // TODO: remove ugly workaround when IE bug is solved
  // http://bugs.jquery.com/ticket/10550#comment:22
  var _fixclonedcheckbox = function(clone) {
    clone.each(function() {
        if ($(this).attr("class") == "_unchecked") {
            $(this).prop("checked", false);
        }
    });
  };

  var get_radio_buttons = function() {
    return $(document).find('[name=templateId]');
  };
  var has_template_selected = function() {
    var buttons = get_radio_buttons();
    var has_checked = false;

    buttons.map(function() {
      if ($(this).attr('checked')) {
        has_checked = true;
      }
    })

    return has_checked;
  };

  var ascertain_dl_button_status = function() {
    var download_button = $('#downloadPDF');

    if (! has_template_selected()) {
      download_button.attr('disabled', 'disabled');
    } else {
      download_button.removeAttr('disabled');
    }
  };

  $('input[name=templateId]:radio').change(function() {
    ascertain_dl_button_status();
  });

  ascertain_dl_button_status();

});