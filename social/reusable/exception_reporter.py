from django import template
from django.views import debug

TECHNICAL_500_TEXT_TEMPLATE = (
    """"""
    """{% firstof exception_type 'Report' %}{% if request %} at {{ request.path_info }}{% endif %}
{% firstof exception_value 'No exception message supplied' %}
{% if request %}
Request Method: {{ request.META.REQUEST_METHOD }}
Request URL: {{ request.get_raw_uri }}{% endif %}
Django Version: {{ django_version_info }}
Python Executable: {{ sys_executable }}
Python Version: {{ sys_version_info }}
Python Path: {{ sys_path }}
Server time: {{server_time|date:"r"}}
Installed Applications:
{{ settings.INSTALLED_APPS|pprint }}
Installed Middleware:
{{ settings.MIDDLEWARE_CLASSES|pprint }}
{% if template_does_not_exist %}Template loader postmortem
{% if postmortem %}Django tried loading these templates, in this order:
{% for entry in postmortem %}
Using engine {{ entry.backend.name }}:
{% if entry.tried %}{% for attempt in entry.tried %}"""
    """    * {{ attempt.0.loader_name }}: {{ attempt.0.name }} ({{ attempt.1 }})
{% endfor %}{% else %}    This engine did not provide a list of tried templates.
{% endif %}{% endfor %}
{% else %}No templates were found because your 'TEMPLATES' setting is not configured.
{% endif %}
{% endif %}{% if template_info %}
Template error:
In template {{ template_info.name }}, error at line {{ template_info.line }}
   {{ template_info.message }}
{% for source_line in template_info.source_lines %}"""
    "{% if source_line.0 == template_info.line %}"
    "   {{ source_line.0 }} : {{ template_info.before }} {{ template_info.during }} {{ template_info.after }}"
    "{% else %}"
    "   {{ source_line.0 }} : {{ source_line.1 }}"
    """{% endif %}{% endfor %}{% endif %}{% if frames %}
Traceback:"""
    "{% for frame in frames %}"
    "{% ifchanged frame.exc_cause %}"
    "  {% if frame.exc_cause %}"
    """
    {% if frame.exc_cause_explicit %}
      The above exception ({{ frame.exc_cause }}) was the direct cause of the following exception:
    {% else %}
      During handling of the above exception ({{ frame.exc_cause }}), another exception occurred:
    {% endif %}
  {% endif %}
{% endifchanged %}
File "{{ frame.filename }}" in {{ frame.function }}
{% if frame.context_line %}  {{ frame.lineno }}. {{ frame.context_line }}{% endif %}
{% endfor %}
{% if exception_type %}Exception Type: {{ exception_type }}{% if request %} at {{ request.path_info }}{% endif %}
{% if exception_value %}Exception Value: {{ exception_value }}{% endif %}{% endif %}{% endif %}
{% if request %}Request information:
GET:{% for k, v in request.GET.items %}
{{ k }} = {{ v|stringformat:"r" }}{% empty %} No GET data{% endfor %}
POST:{% for k, v in filtered_POST.items %}
{{ k }} = {{ v|stringformat:"r" }}{% empty %} No POST data{% endfor %}
FILES:{% for k, v in request.FILES.items %}
{{ k }} = {{ v|stringformat:"r" }}{% empty %} No FILES data{% endfor %}
COOKIES:{% for k, v in request.COOKIES.items %}
{{ k }} = {{ v|stringformat:"r" }}{% empty %} No cookie data{% endfor %}
META:{% for k, v in request.META.items|dictsort:"0" %}
{{ k }} = {{ v|stringformat:"r" }}{% endfor %}
{% else %}Request data not supplied
{% endif %}
Settings:
Using settings module {{ settings.SETTINGS_MODULE }}{% for k, v in settings.items|dictsort:"0" %}
{{ k }} = {{ v|stringformat:"r" }}{% endfor %}
{% if not is_email %}
You're seeing this error because you have DEBUG = True in your
Django settings file. Change that to False, and Django will
display a standard page generated by the handler for this status code.
{% endif %}
"""
)


class CustomExceptionReporter(debug.ExceptionReporter):
    def get_traceback_text(self):
        t = debug.DEBUG_ENGINE.from_string(TECHNICAL_500_TEXT_TEMPLATE)
        c = template.Context(
            self.get_traceback_data(), autoescape=False, use_l10n=False
        )
        return t.render(c)
