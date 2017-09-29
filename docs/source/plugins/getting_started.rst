Getting started with Indico plugins
===================================

.. todo::
    Write a **REAL**, simple example of a plugin. Include link to Github repo.

Example plugin
--------------

The following is a minimal plugin that makes use of all capababilites of the plugin API. The **display name** of the
plugin is defined by the first line of the docstring and the **description** by the rest of it. The plugin may override
signal handlers to hook into Indico and aditionally run any initialization needed. For example, it will add some
command to Indico CLI, extend the shell context and register some assets. Also, `init` is used to inject CSS and JS
bundles outside of the plugin scope. ::

    class ExamplePlugin(IndicoPlugin):
        """Example Plugin

        An example plugin that demonstrates the capabilities of the new Indico plugin system.
        """

        settings_form = SettingsForm

        def init(self):
            super(ExamplePlugin, self).init()
            self.inject_css('global_css')
            self.inject_js('global_js')

        def get_blueprints(self):
            return blueprint

        def add_cli_command(self, manager):
            @manager.command
            @with_plugin_context(self)
            def example():
                """Example command from example plugin"""
                print 'example plugin says hi', current_plugin
                if self.settings.get('show_message'):
                    print self.settings.get('dummy_message')

        def extend_shell_context(self, add_to_context):
            add_to_context('bar', name='foo', doc='foobar from example plugin', color='magenta!')

        def register_assets(self):
            self.register_js_bundle('example_js', 'js/example.js')
            self.register_js_bundle('global_js', 'js/global.js')
            self.register_css_bundle('example_css', 'css/example.scss')
            self.register_css_bundle('global_css', 'css/global.scss')


The plugin can specify its settings via a :class:`~indico.web.forms.base.IndicoForm`::

    class SettingsForm(IndicoForm):
        dummy_message = StringField('Dummy Message')
        show_message = BooleanField('Show Message')


The plugin can also specify request handlers and templates. Templates will be loaded from a `templates` folder within
your plugin folder. Your plugin can even load templates from other modules by prefixing the name of the template
`'other_plugin:example'` with `render_template()`. ::

    class WPExample(WPDecorated):
        def _getBody(self, params):
            return render_plugin_template('example.html', **params)


    class RHExample(RH):
        def _process(self):
            return WPExample(self, foo=u'bar').display()


    class RHTest(RH):
        def _process(self):
            return render_plugin_template('test.html')


    blueprint = IndicoPluginBlueprint('example', __name__)
    blueprint.add_url_rule('/example', 'example', view_func=RHExample)
    blueprint.add_url_rule('/example/x', 'example', view_func=RHExample)
    blueprint.add_url_rule('/test', 'test', view_func=RHTest)
