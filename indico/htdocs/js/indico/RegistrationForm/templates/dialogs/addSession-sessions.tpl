<form>
    {% for el in sessions %}
        <input type="checkbox" name="session" value="{{ el.id }}">{{ el.caption }}</input>
    {% endfor %}
</form>
