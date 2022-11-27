from django.core.paginator import Paginator
from django.db.models import QuerySet


def posts_paginator(request, post_list: QuerySet, posts_count: int):
    paginator = Paginator(post_list, posts_count)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
