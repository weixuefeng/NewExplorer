from django.conf.urls import patterns, include, url
from django.conf import settings
from django.contrib import admin
from django.views.static import serve as serve_static
from django.views.decorators.cache import never_cache
from django.views.generic import TemplateView, RedirectView

urlpatterns = patterns('',
                       url(r'^$', 'welcome.views.home'),
                       url(r'^block', 'welcome.views.home'),
                       url(r'^status', 'welcome.views.home'),
                       url(r'^address', 'welcome.views.home'),
                       url(r'^addrs', 'welcome.views.home'),
                       url(r'^tx', 'welcome.views.home'),
                       url(r'^transactions', 'welcome.views.home'),
                       url(r'^address', 'welcome.views.home'),
                       url(r'^contracts', 'welcome.views.home'),
                       url(r'^contract', 'welcome.views.home'),
                       url(r'^api/v(?P<version>[0-9]+)/', include('api.urls')),
                       url(r'^dashboard', 'api.apis.api_for_dashboard'),
)

if settings.DEBUG:
    urlpatterns += patterns('', url(r'^js/(?P<path>.*)$', never_cache(serve_static),
                                    {'document_root': '%s/templates/ui/public/js' % (settings.PROJECT_ROOT), 'show_indexes': True}))
    urlpatterns += patterns('', url(r'^css/(?P<path>.*)$', never_cache(serve_static),
                                    {'document_root': '%s/templates/ui/public/css' % (settings.PROJECT_ROOT), 'show_indexes': True}))
    urlpatterns += patterns('', url(r'^views/(?P<path>.*)$', never_cache(serve_static),
                                    {'document_root': '%s/templates/ui/public/views' % (settings.PROJECT_ROOT), 'show_indexes': True}))
    urlpatterns += patterns('', url(r'^img/(?P<path>.*)$', never_cache(serve_static),
                                    {'document_root': '%s/templates/ui/public/img' % (settings.PROJECT_ROOT), 'show_indexes': True}))
    urlpatterns += patterns('', url(r'^fonts/(?P<path>.*)$', never_cache(serve_static),
                                    {'document_root': '%s/templates/ui/public/fonts' % (settings.PROJECT_ROOT), 'show_indexes': True}))
    urlpatterns += patterns('', url(r'^lib/(?P<path>.*)$', never_cache(serve_static),
                                    {'document_root': '%s/templates/ui/public/lib' % (settings.PROJECT_ROOT), 'show_indexes': True}))

