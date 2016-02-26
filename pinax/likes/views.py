from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseForbidden, JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template import RequestContext
from django.template.loader import render_to_string
from django.views.generic import View

from pinax.likes.models import Like
from pinax.likes.signals import object_liked, object_unliked
from pinax.likes.utils import widget_context

try:
    from account.mixins import LoginRequiredMixin
except ImportError:
    from django.contrib.auth.mixins import LoginRequiredMixin


class LikeToogleView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        content_type = get_object_or_404(ContentType, pk=self.kwargs.get('content_type_id'))
        obj = content_type.get_object_for_this_type(pk=self.kwargs.get('object_id'))

        if not request.user.has_perm("likes.can_like", obj):
            return HttpResponseForbidden()

        like, liked = Like.like(request.user, content_type, obj.id)

        if liked:
            object_liked.send(sender=Like, like=like, request=request)
        else:
            object_unliked.send(sender=Like, object=obj, request=request)

        if request.is_ajax():
            html_ctx = widget_context(request.user, obj)
            template = "pinax/likes/_widget.html"
            if request.GET.get("t") == "b":
                template = "pinax/likes/_widget_brief.html"
            data = {
                "html": render_to_string(
                    template,
                    html_ctx,
                    context_instance=RequestContext(request)
                ),
                "likes_count": html_ctx["like_count"],
                "liked": html_ctx["liked"],
            }
            return JsonResponse(data)
        return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))

