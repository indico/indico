type('CurrencyDialog', ['ConfirmPopupWithPM'], {

}, function(title, handler, old_data) {

    this.currency_name = Html.input({}, 'text', old_data ? old_data.name : null);
    this.currency_abbrev = Html.input({}, 'text', old_data ? old_data.abbrev : null);

    var form = $("<div></div>").append(
                        IndicoUtil.createFormFromMap([
                            [$T('Currency name'), this.currency_name],
                            [$T('Currency abbreviation'), this.currency_abbrev]]),
                        $("<div style='color: orange; font-size: smaller;'></div>").append($T('Example: Euro and EUR')));

    this.ConfirmPopupWithPM(title, form, handler);
    this.parameterManager.add(this.currency_name, 'text', false);
    this.parameterManager.add(this.currency_abbrev, 'text', false);
});


function request(method, params, close) {
    var killProgress = IndicoUI.Dialogs.Util.progress($T("Processing..."));

    indicoRequest(method, params,
        function(result, error) {
            killProgress();
            close();

            if (!error && result.success) {
                render_table(result.table);
            } else {
                IndicoUtil.errorReport(error);
            }
        });
}


function remove_currency(name) {
    indicoRequest(
        'epayment.removeCurrency',
        { name: name },
        function(result, error) {
            if (!error){
                render_table(result.table);
                    }
            else{
                IndicoUtil.errorReport(error);
            }
        }
    );
}


function edit_currency(oldName, oldAbbreviation){
    var edit_popup = new CurrencyDialog(
        $T('Edit currency'),
        function(value){
            if(value){
                request('epayment.editCurrency', {
                    name: this.currency_name.get(),
                    oldName: oldName,
                    abbreviation: this.currency_abbrev.get()
                }, _.bind(function() {
                    this.close();
                }, this));
            }
        }, {
            name: oldName,
            abbrev: oldAbbreviation
        });

    edit_popup.open();
}


var render_table = function(table) {
    var table_elem = $('<table id="currencies"/>')
    table_elem.append($('<tr><th>' + $T('Currency name') + '</th><th>' + $T('Currency Abbreviation') + '</th><td></td></tr>'))

    _.each(table, function(currency){
        var removeButton = $('<a href="#"/>').append(IndicoUI.Buttons.removeButton().dom).click(function(){
            remove_currency(currency.name);
            return false;
        });

        var editButton = $('<a href="#"/>').append(IndicoUI.Buttons.editButton().dom).click(function(){
            edit_currency(currency.name, currency.abbreviation);
            return false;
        });

        var row = $('<tr><td>' + currency.name + '</td><td>' + currency.abbreviation + '</td></tr>')

        row.append($('<td/>').append(editButton, removeButton));

        table_elem.append(row);
    });

    $('#currenciesContainer').html('');
    $('#currenciesContainer').append(table_elem);
};


$(function() {
    var popupTitle = $T('Enter the currency full name and the abreviation');

    render_table(currencies);

    $('#currencies').append(
        $('<button>' + $T('Add new currency') + '</button>').click(function() {
            var currenciesPopup = new CurrencyDialog(
                popupTitle,
                function(value){
                    if(value){
                        request('epayment.addCurrency', {
                            name: this.currency_name.get(),
                            abbreviation: this.currency_abbrev.get()
                        }, _.bind(function() {
                            this.close();
                        }, this));
                    }
                });
            currenciesPopup.open();
    }));
});
