from django import template
from django.views import debug

TECHNICAL_500_TEXT_TEMPLATE = """ 
This is a template error
"""


class CustomExceptionReporter(debug.ExceptionReporter):
    def get_traceback_text(self):
        t = debug.DEBUG_ENGINE.from_string(TECHNICAL_500_TEXT_TEMPLATE)
        c = template.Context(
            self.get_traceback_data(), autoescape=False, use_l10n=False
        )
        return t.render(c)
