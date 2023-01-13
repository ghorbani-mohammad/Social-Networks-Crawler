from django import template
from django.views import debug

TECHNICAL_500_TEXT_TEMPLATE = """
{% firstof exception_type 'Report' %}{% if request %} at {{ request.path_info }}{% endif %}
{% firstof exception_value 'No exception message supplied' %}
{% if request %}
  Request Method: {{ request.META.REQUEST_METHOD }}
  Request URL: {{ request.get_raw_uri }}
{% endif %}
Django Version: {{ django_version_info }}
Python Executable: {{ sys_executable }}
Python Version: {{ sys_version_info }}
Python Path: {{ sys_path }}
Server time: {{server_time|date:"r"}}
Installed Applications:
  {{ settings.INSTALLED_APPS|pprint }}
Installed Middleware:
  {{ settings.MIDDLEWARE_CLASSES|pprint }}
"""


class CustomExceptionReporter(debug.ExceptionReporter):
    def get_traceback_text(self):
        t = debug.DEBUG_ENGINE.from_string(TECHNICAL_500_TEXT_TEMPLATE)
        c = template.Context(
            self.get_traceback_data(), autoescape=False, use_l10n=False
        )
        return t.render(c)
