from django.urls import path

from . import views
from . import ajax

urlpatterns = [
    path('', views.index, name='index'),
    path('index', views.index, name='index'),
    path('get_subcategories/', ajax.subcategories,
        name='subcategories'),
    path('get_books/', ajax.books, name='books'),
    path('get_chapters/', ajax.chapters, name='chapters'),
    path('get_examples/', ajax.examples, name='examples'),
    path('get_revisions/', ajax.revisions, name='revisions'),
    path('get_code/', ajax.code, name='code'),
    path('get_diff/', ajax.diff, name='diff'),
    path('update_view_count/', views.update_view_count,
        name='update_view_count')
    ]
