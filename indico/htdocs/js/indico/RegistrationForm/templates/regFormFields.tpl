<table class="{{ classes.fieldDisabled if field.disabled else classes.field }}" id="{{ field.id }}" >
    <tr>
        <td class="regFormCaption">
            <span class="regFormCaption">{{ field.caption }}</span>
            {% if field.mandatory %}
                <span class="regFormMandatoryField">*</span>
            {% endif %}
        </td>
        <td>
            {% block field %}
            {% endblock %}
        </td>
    </tr>
</table>

{#
<script type="text/template" id="itemWrapAllRight">
<table class="{{ classes.fieldDisabled if field.disabled else classes.field }}" id="{{ field.id }}">
    <tr>
      <td class="regFormCaption">
      </td>
      <td>
          {{ item }}
      </td>
    </tr>
</table>
</script>
#}
