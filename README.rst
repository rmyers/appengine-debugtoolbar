Appengine Debug Toolbar
=======================

This is a fork of the awesome django debug toolbar:

https://github.com/django-debug-toolbar/django-debug-toolbar

It is designed to work with webapp and jinja the default
wsgi 'framework' for Appengine.

Example::

    from google.appengine.ext.webapp import WSGIApplication
    from google.appengine.ext.webapp.util import run_wsgi_app
    from appengine_debugtoolbar.middleware import DebugToolbar

    urls = [...]
    
    config = {
       'INTERCEPT_REDIRECTS': True,
       'JINJA_TEMPLATEDIR': 'templates',
    }
    
    app = DebugToolbar(WSGIApplication(urls, debug=True), config)

    def main():
        run_wsgi_app(app) 

Then you'll need to update other things
lskj
