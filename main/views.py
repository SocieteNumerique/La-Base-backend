from django.http import JsonResponse


def version(_):
    return JsonResponse({"version": "0.0.1"})
