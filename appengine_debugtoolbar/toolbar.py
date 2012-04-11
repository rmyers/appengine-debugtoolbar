"""
The main DebugToolbar class that loads and renders the Toolbar.
"""
import os
import os.path

from django.utils.datastructures import SortedDict
import logging

class DebugToolbar(object):

    def __init__(self, request, jinja_env, config={}):
        self.request = request
        self.jinja_env = jinja_env
        self._panels = SortedDict()
        base_url = self.request.environ.get('SCRIPT_NAME', '')
        self.config = {
            'INTERCEPT_REDIRECTS': True,
        }
        # Check if settings has a DEBUG_TOOLBAR_CONFIG and updated config
        self.config.update(config)
        self.template_context = {
            'BASE_URL': base_url,  # for backwards compatibility
            'DEBUG_TOOLBAR_MEDIA_URL': self.config.get('MEDIA_URL'),
        }

        load_panel_classes(self.config)
        self.load_panels()
        self.stats = {}

    def _get_panels(self):
        return self._panels.values()
    panels = property(_get_panels)

    def get_panel(self, cls):
        return self._panels[cls]

    def load_panels(self):
        """
        Populate debug panels
        """
        global panel_classes
        for panel_class in panel_classes:
            try:
                panel_instance = panel_class(context=self.template_context)
            except:
                logging.exception('Problem loading panel')
                raise  # Bubble up problem loading panel

            self._panels[panel_class] = panel_instance

    def render_toolbar(self):
        """
        Renders the overall Toolbar with panels inside.
        """
        media_path = os.path.join(os.path.dirname(__file__), 'media', 'debug_toolbar')

        context = self.template_context.copy()
        context.update({
            'panels': self.panels,
            'js': open(os.path.join(media_path, 'js', 'toolbar.min.js'), 'r').read(),
            'css': open(os.path.join(media_path, 'css', 'toolbar.min.css'), 'r').read(),
        })
        logging.error(self.panels)
        
        template = self.jinja_env.get_template('debug_toolbar/base.html')
        return template.render(**context)


panel_classes = []


def load_panel_classes(config):

    # Check if settings has a DEBUG_TOOLBAR_PANELS, otherwise use default
    panels = config.get('DEBUG_TOOLBAR_PANELS', (
        'appengine_debugtoolbar.panels.version.VersionDebugPanel',
        'appengine_debugtoolbar.panels.timer.TimerDebugPanel',
        'appengine_debugtoolbar.panels.headers.HeaderDebugPanel',
        'appengine_debugtoolbar.panels.request_vars.RequestVarsDebugPanel',
        # 'appengine_debugtoolbar.panels.cache.CacheDebugPanel',
        'appengine_debugtoolbar.panels.appstats.AppstatsDebugPanel',
        'appengine_debugtoolbar.panels.logger.LoggingPanel',
    ))
    for panel_path in panels:
        try:
            dot = panel_path.rindex('.')
        except ValueError:
            raise Exception(
                '%s isn\'t a debug panel module' % panel_path)
        panel_module, panel_classname = panel_path[:dot], panel_path[dot + 1:]
        mod = __import__(panel_module, {}, {}, [''])
        panel_class = getattr(mod, panel_classname)
        panel_classes.append(panel_class)
