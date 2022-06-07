from djangorestframework_camel_case.render import CamelCaseBrowsableAPIRenderer


class RendererNoForm(CamelCaseBrowsableAPIRenderer):
    def show_form_for_method(self, view, method, request, obj):
        return False
