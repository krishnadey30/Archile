from .views import *
from django.urls import path,re_path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('',index,name="index"),
    path('login',login,name="login"),
    path('logout',user_logout,name="logout"),
    re_path('archile/auth/user/(?P<token_id>[\w\.-]+)/',home,name="home"),
    path('search/<str:query>',search,name="search"),
    path('search_box',search_box,name="search_box"),
    path('create_channel',create_channel,name="create_channel"),
    path('create_post/<int:c_id>',create_post,name="create_post"),
    path('save_post/',save_post,name="save_post"),
    path('edit_post/',edit_post,name="edit_post"),
    path('post/<int:p_id>',post,name="post"),
    path('channel/<int:c_id>',channel,name="channel"),
    path('subscribe_channel/<int:c_id>',subscribe_channel,name="subscribe_channel"),
    path('edit_channel/<int:c_id>',edit_channel,name="edit_channel"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)