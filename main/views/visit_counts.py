import datetime

from rest_framework.decorators import api_view
from rest_framework.response import Response

from main.models.visit_counts import ResourceVisit, BaseVisit, hash_ip


def get_client_ip(request):
    if ip := request.META.get("X-Real-IP"):
        return ip
    if ip := request.META.get("HTTP_X_FORWARDED_FOR"):
        return ip
    if ip := request.META.get("REMOTE_ADDR"):
        return ip
    return None


@api_view(["GET"])
def increment_visit_count(request, object_type, pk):
    if object_type == "resource":
        model = ResourceVisit
    elif object_type == "base":
        model = BaseVisit
    else:
        raise NotImplementedError()

    if not (ip := get_client_ip(request)):
        return Response()

    ip_hash = hash_ip(ip)
    # add view if it does not already exists
    if not model.objects.filter(
        instance_id=pk, ip_hash=ip_hash, date=datetime.date.today()
    ).exists():
        model.objects.create(instance_id=pk, ip_hash=ip_hash)

    return Response()
