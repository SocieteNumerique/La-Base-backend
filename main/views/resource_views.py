import collections
import shutil
import tempfile

from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from rest_framework import mixins, viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from main.models import Criterion
from main.models.models import Resource
from main.models.contents import ContentBlock, ContentSection
from main.query_changes.permissions import (
    resources_queryset_for_user,
    bases_queryset_for_user,
)
from main.query_changes.stats_annotations import resources_queryset_with_stats
from main.serializers.base_resource_serializers import (
    FullResourceSerializer,
    ShortResourceSerializer,
    MarkDuplicatesResourceSerializer,
)
from main.serializers.content_serializers import (
    ReadContentSerializer,
    WriteContentSerializer,
    ContentOrderSerializer,
    ContentBySectionSerializer,
    ContentSectionSerializer,
)
from main.serializers.evaluation_serializers import EvaluationSerializer
from main.views.base_views import generic_pin_action
from moine_back import settings


class ResourceHasWriteAccessFilter(filters.BaseFilterBackend):
    """
    Filter only writable ressource for user for patch/delete requests.
    """

    def filter_queryset(self, request: HttpRequest, queryset, view):
        if request.method in ["PATCH", "DELETE", "PUT"]:
            return queryset.filter(can_write=True)

        # GET does not need additional filtering
        return queryset


class UserCanWriteOnBaseForPost(BasePermission):
    def has_permission(self, request, view):
        if request.method != "POST" or not request.data:
            return True

        return (
            bases_queryset_for_user(request.user)
            .filter(can_add_resources=True)
            .filter(pk=request.data["root_base"])
            .exists()
        )


def order_action(model, serializer_class, request):
    res_data = []
    for instance_id, data in request.data.items():
        instance = model.objects.get(pk=instance_id)
        serializer = serializer_class(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        if getattr(instance, "_prefetched_objects_cache", None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        res_data.append(serializer.data)
    queryset = model.objects.filter(id__in=request.data.keys()).all()
    return Response(serializer_class(queryset, many=True).data)


class ResourceView(
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = FullResourceSerializer
    filter_backends = [ResourceHasWriteAccessFilter]
    permission_classes = [UserCanWriteOnBaseForPost]

    def get_queryset(self):
        return resources_queryset_with_stats(
            resources_queryset_for_user(self.request.user)
        )

    @action(detail=True, methods=["GET"])
    def contents(self, request, pk=None):
        # TODO optimize queryset to avoid later content tags requests:
        #  prefetch("contents__tags") doesn't help
        obj: Resource = self.get_object()
        serializer = ContentBySectionSerializer(
            obj, context=self.get_serializer_context()
        )
        return Response(serializer.data)

    @action(detail=True, methods=["GET"])
    def short(self, request, pk=None):
        instance = self.get_object()
        serializer = ShortResourceSerializer(
            instance, context=self.get_serializer_context()
        )
        return Response(serializer.data)

    @action(detail=True, methods=["PATCH"])
    def pin(self, request, pk=None):
        return generic_pin_action(Resource, self, request, pk)

    @action(detail=True, methods=["PATCH"])
    def mark_duplicates(self, request, pk):
        resource = self.get_object()
        resource.ignored_duplicates.add(*request.data.get("ignored_duplicates"))
        resource.confirmed_duplicates.add(*request.data.get("confirmed_duplicates"))
        serializer = MarkDuplicatesResourceSerializer(resource)

        return Response(serializer.data)

    @action(detail=True, methods=["GET"], url_path="files")
    def export_files(self, request, pk):
        """Download all files from resources locally, create zip file and serve it."""
        resource: Resource = self.get_object()
        errors = []
        with tempfile.TemporaryDirectory() as tmp_dir:
            # saving files in temporary dir
            for file in resource.contents.filter(filecontent__isnull=False):
                with open(f"{tmp_dir}/{file.filecontent.file.name}", "wb") as write_fh:
                    try:
                        with file.filecontent.file.open() as read_fh:
                            write_fh.write(read_fh.read())
                    except Exception:
                        errors.append(file.filecontent.file.name)

            # creating zip
            with tempfile.NamedTemporaryFile() as tmp_file:
                shutil.make_archive(tmp_file.name, "zip", tmp_dir)

                # serve archive
                with open(f"{tmp_file.name}.zip", "rb") as fh:
                    data = fh.read()
                response = HttpResponse(data, content_type="application/zip")
                response[
                    "Content-Disposition"
                ] = f"attachment; filename={resource.title} - fichiers.zip"
                return response

    @action(detail=True, methods=["GET"], url_path="evaluations")
    def list_evaluations(self, request, pk):
        """List evaluations with stats per criterion."""
        evaluation_grades = range(0, 5)
        reco_grades = range(0, 2)
        resource: Resource = self.get_object()
        if resource.can_evaluate:
            evaluations = list(resource.evaluations.all())
        else:
            evaluations = []
        criteria = Criterion.objects.all()
        to_return = {}
        for criterion in criteria:
            evaluations_for_criterion = [
                evaluation
                for evaluation in evaluations
                if evaluation.criterion_id == criterion.slug
            ]
            grades = collections.Counter()
            for grade in (
                reco_grades if criterion.slug == "recommendation" else evaluation_grades
            ):
                grades[grade] = 0
            for evaluation in evaluations_for_criterion:
                grades[evaluation.evaluation] += 1
            to_return[criterion.slug] = {
                "evaluations": [
                    EvaluationSerializer(evaluation, context={"request": request}).data
                    for evaluation in evaluations
                    if evaluation.criterion_id == criterion.slug
                ],
                "stats": {"grades": grades, "count": len(evaluations_for_criterion)},
            }

        return Response(to_return)


class RessourceDuplicatesValidatorViews(APIView):
    trigram_similarity_threshold = 0.5

    def get_queryset(self):
        return resources_queryset_with_stats(
            resources_queryset_for_user(self.request.user)
        )

    def post(self, request, pk):
        resource_title = request.data.get("title") or ""
        resource_description = request.data.get("description") or ""
        instance = self.get_queryset().get(id=pk)
        excluded_resource = [
            pk,
            *instance.ignored_duplicates.values_list("id", flat=True),
            *instance.confirmed_duplicates.values_list("id", flat=True),
        ]
        queryset_resources = self.get_queryset()

        queryset_resources = queryset_resources.exclude(id__in=excluded_resource)
        if settings.IS_POSTGRESQL_DB:
            queryset_resources = queryset_resources.annotate(
                title_similarity=TrigramSimilarity("title", resource_title),
                description_similarity=TrigramSimilarity(
                    "description", resource_description
                ),
            ).filter(
                Q(title_similarity__gt=self.trigram_similarity_threshold)
                | Q(description_similarity__gt=self.trigram_similarity_threshold)
            )
        else:
            queryset_resources = queryset_resources.filter(
                Q(title=resource_title) | Q(description=resource_description)
            )
        return Response(queryset_resources.values_list("id", flat=True))


class ContentView(
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    def get_queryset(self):
        return ContentBlock.objects.filter(
            resource__in=resources_queryset_for_user(self.request.user)
        )

    def get_serializer_context(self):
        context = super(ContentView, self).get_serializer_context()
        context.update({"request": self.request})
        return context

    def get_serializer_class(self):
        if self.action in ["retrieve", "list"]:
            return ReadContentSerializer
        return WriteContentSerializer

    def create(self, request, *args, **kwargs):
        is_many = isinstance(request.data, list)
        serializer = self.get_serializer(data=request.data, many=is_many)
        # from here it is the package's function
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    @action(detail=False, methods=["PATCH"])
    def order(self, request):
        return order_action(ContentBlock, ContentOrderSerializer, request)


class SectionView(
    viewsets.GenericViewSet,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
):
    def get_queryset(self):
        return ContentSection.objects.filter(
            resource__in=resources_queryset_for_user(self.request.user)
        )

    def get_serializer_class(self):
        return ContentSectionSerializer

    @action(detail=False, methods=["PATCH"])
    def order(self, request):
        return order_action(ContentSection, ContentSectionSerializer, request)
