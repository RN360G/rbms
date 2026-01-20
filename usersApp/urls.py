from django.urls import path
from usersApp import views

urlpatterns = [
    path('', views.user, name='user'),
    path('newuser/', views.NewUser.as_view(), name='newUser'),
    path('accessandrole<userID>', views.AccessAndRoles.as_view(), name='accessAndRoles'),
    path('edituser/<userID>', views.EditUser.as_view(), name='editUser'),
    path('youractivities', views.yourActivityLogs, name='yourActivityLogs'),
    path('yourprofile', views.profile, name='profile'),
    path('uploadprofileimage', views.UploadProfileImage.as_view(), name='uploadProfileImage'),

]