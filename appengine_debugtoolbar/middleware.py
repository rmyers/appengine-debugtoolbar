import thread
import os
from webob import Request
from appengine_debugtoolbar.toolbar import DebugToolbar

import jinja2
import logging

# TODO: centralize this
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates')

environment = jinja2.Environment(
	loader=jinja2.FileSystemLoader(TEMPLATE_DIR),
	extensions=['jinja2.ext.i18n'],
	autoescape=True)

# TODO: check for babel?
environment.install_gettext_callables(
    lambda x: x,
    lambda m, r, n: m,
    False
)

def replace_insensitive(string, target, replacement):
    """
    Similar to string.replace() but is case insensitive
    Code borrowed from: http://forums.devshed.com/python-programming-11/case-insensitive-string-replace-490921.html
    """
    no_case = string.lower()
    index = no_case.rfind(target.lower())
    if index >= 0:
        return string[:index] + replacement + string[index + len(target):]
    else:  # no results so return the original string
        return string

class DebugToolbarMiddleware(object):
    """
    Middleware to set up Debug Toolbar on incoming request and render toolbar
    on outgoing response.
    """
    debug_toolbars = {}

    @classmethod
    def get_current(cls):
        return cls.debug_toolbars.get(thread.get_ident())

    def __init__(self, app, config=None):
        self._urlconfs = {}
        self.config = config or {}
        self.app = app

        show_toolbar_callback = self.config.get('SHOW_TOOLBAR_CALLBACK', 
			self._show_toolbar)
        self.show_toolbar = show_toolbar_callback

        tag = self.config.get('TAG', u'body')
        self.tag = u'</%s>' % tag
        
        self.internal_ips = self.config.get('INTERNAL_IPS', ['127.0.0.1'])

    def _show_toolbar(self, request):
        x_forwarded_for = request.environ.get('HTTP_X_FORWARDED_FOR', None)
        if x_forwarded_for:
            remote_addr = x_forwarded_for.split(',')[0].strip()
        else:
            remote_addr = request.environ.get('REMOTE_ADDR', None)

        # TODO: allow in production or not?
        return remote_addr in self.internal_ips

    def __call__(self, environ, start_response):
        #__traceback_hide__ = True
        
        req = Request(environ)

        if self.show_toolbar(req):
            toolbar = DebugToolbar(req, environment, self.config)
            for panel in toolbar.panels:
                panel.process_request(req)
            self.__class__.debug_toolbars[thread.get_ident()] = toolbar

            def dummy(self, request):
                pass

            self.process_view(req, dummy, [], {})
            resp = req.get_response(self.app)
            resp.charset = 'utf-8'
            
            self.process_response(req, resp)
        else:
            resp = req.get_response(self.app)
        
        return resp(environ, start_response)


    def process_view(self, request, view_func, view_args, view_kwargs):
        #__traceback_hide__ = True
        toolbar = self.__class__.debug_toolbars.get(thread.get_ident())
        if not toolbar:
            return
        for panel in toolbar.panels:
            panel.process_view(request, view_func, view_args, view_kwargs)

    def process_response(self, request, response):
        #__traceback_hide__ = True
        ident = thread.get_ident()
        toolbar = self.__class__.debug_toolbars.get(ident)
        if not toolbar:
            return response
        if response.status in [301, 302, 303, 304]:
            if not toolbar.config['INTERCEPT_REDIRECTS']:
                return response
            redirect_to = response.get('Location', None)
            if redirect_to:
                cookies = response.cookies
                template = environment.get_template('debug_toolbar/redirect.html')
                response = template.render(redirect_to=redirect_to)
                response.cookies = cookies
        for panel in toolbar.panels:
            panel.process_response(request, response)
        response.unicode_body = replace_insensitive(
                response.unicode_body,
                self.tag,
                toolbar.render_toolbar() + self.tag)
        if response.headers.get('Content-Length', None):
            response.headers['Content-Length'] = len(response.body)
        del self.__class__.debug_toolbars[ident]
        return response
