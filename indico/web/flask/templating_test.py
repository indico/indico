import pytest
from flask import render_template_string


class TestEnsureUnicodeExtension:
    def _render(self, template, raises=None):
        val = u'm\xf6p'
        utfval = val.encode('utf-8')
        func = lambda x: x.encode('utf-8').decode('utf-8')
        if raises:
            with pytest.raises(raises):
                render_template_string(template, val=utfval, func=func)
        else:
            assert (render_template_string(template, val=val, func=func)
                    == render_template_string(template, val=utfval, func=func))

    def test_simple_vars(self):
        """Test simple variables"""
        self._render('{{ val }}')

    def test_func_args(self):
        """Test function arguments (no automated unicode conversion!)"""
        self._render('{{ func(val | ensure_unicode) }}')
        self._render('{{ func(val) }}', UnicodeDecodeError)

    def test_filter_vars(self):
        """Test variables with filters"""
        self._render('{{ val | ensure_unicode }}')  # Redundant but needs to work nonetheless
        self._render('{{ val | safe }}')

    def test_inline_if(self):
        """Test variables with inline if"""
        self._render('x {{ val if true else val }} x {{ val if false else val }} x')
        self._render('x {{ val|safe if true else val|safe }} x {{ val|safe if false else val|safe }} x')

    def test_trans(self):
        """Test trans tag which need explicit unicode conversion"""
        self._render('{% trans x=val | ensure_unicode %}{{ x }}}{% endtrans %}')
        self._render('{% trans x=val %}{{ x }}}{% endtrans %}', UnicodeDecodeError)
