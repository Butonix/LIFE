from django.urls import path

from . import views

urlpatterns = [
    path('api/enter_chat_room', views.enter_chat_room, name='enter_chat_room'),
    path('api/user_sign_up', views.user_sign_up, name='user_sign_up'),
    path('api/check_logged_in', views.check_logged_in, name='check_logged_in'),
    path('api/create_new_post', views.create_new_post, name='create_new_post'),
    path('api/like_a_post', views.like_a_post, name='like_a_post'),
    path('api/delete_a_post', views.delete_a_post, name='delete_a_post'),
    path('api/add_a_comment', views.add_a_comment, name='add_a_comment'),
    path('api/read_notifications', views.read_notifications, name='read_notifications'),
    path('api/follow_user', views.follow_user, name='follow_user'),
    path('api/get_home_feed', views.get_home_feed, name='get_home_feed'),
    path('api/get_user_profile', views.get_user_profile, name='get_user_profile'),
    path('api/check_profile_name_availability', views.check_profile_name_availability, name='check_profile_name_availability'),
    path('api/upload_picture', views.upload_picture, name='upload_picture'),
    path('api/upload_avatar', views.upload_avatar, name='upload_avatar'),
    path('api/search', views.search, name='search'),
    path('api/get_trending_hashtags', views.get_trending_hashtags, name='get_trending_hashtags'),
    path('api/add_or_remove_bookmark', views.add_or_remove_bookmark, name='add_or_remove_bookmark'),
    path('api/get_bookmark', views.get_bookmark, name='get_bookmark'),
    path('api/network_analysis', views.network_analysis, name='network_analysis'),
    path('api/create_mass_users', views.create_mass_users, name='create_mass_users'),
    path('api/create_random_connections', views.create_random_connections, name='create_random_connections'),
    path('api/create_random_interactions', views.create_random_interactions, name='create_random_interactions'),
    path('api/following_recommendation', views.following_recommendation, name='following_recommendation'),
    path('api/clear_db_data', views.clear_db_data, name='clear_db_data'),
]