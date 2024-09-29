from django.conf import settings
from django_hosts import patterns, host

host_patterns = patterns(
    "",
    host(r"www", settings.ROOT_URLCONF, name="www"),
    host(r"api", "subdomains.api", name="api"),
    host(r"admin", "subdomains.admin", name="admin"),
    # TODO: Add static file subdomain
    host(r"static", "subdomains.static", name="static"),
)
