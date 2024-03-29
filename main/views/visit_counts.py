import datetime

from rest_framework.decorators import api_view
from rest_framework.response import Response

from main.models import Resource, Base
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
        model_visit, model = ResourceVisit, Resource
    elif object_type == "base":
        model_visit, model = BaseVisit, Base
    else:
        raise NotImplementedError()

    if not (ip := get_client_ip(request)):
        return Response()

    try:
        instance = model.objects.get(pk=pk)
    except model.DoesNotExist:
        # ignore visits of non-existing objects
        return Response()

    # ignore visits of superusers
    if request.user.is_superuser:
        return Response()

    # ignore visits of base owner
    if object_type == "base" and instance.owner == request.user:
        return Response()
    # ignore visits of resources when user is the base owner
    if object_type == "resource" and instance.root_base.owner == request.user:
        return Response()

    ip_hash = hash_ip(ip)
    # add view if it does not already exists
    if not model_visit.objects.filter(
        instance_id=pk, ip_hash=ip_hash, date=datetime.date.today()
    ).exists():
        model_visit.objects.create(instance_id=pk, ip_hash=ip_hash)

    return Response()
