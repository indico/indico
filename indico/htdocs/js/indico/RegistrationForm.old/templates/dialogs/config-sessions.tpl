<form>
    <div class="regFormDialogEditLine">
        <label class="regFormDialogCaption" style="width : 180px">{% _ "Type of sessions' form" %}</label>
        <select name="type">
            <option value="2priorities" {{ "selected" if type == "2priorities" }}>
                {% _ '2 choices' %}
            </option>
            <option value="all" {{ "selected" if type == "all" }}>{% _ 'multiple' %}</option>
        </select>
    </div>
    <span> {% _ 'How many sessions the registrant can choose.' %}
        <br> {% _ 'Please note that billing is not possible when using 2 choices' %}
    </span>
</form>
