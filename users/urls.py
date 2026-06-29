from django.urls import path, re_path
from .views import (
    RegisterView,
    VerifyEmailView,
    ResendVerificationCodeView,
    LoginView,
    TokenRefreshView,
    LogoutView,
    ChangePasswordView,


    MeView,
    UpdateProfileView,
    UpdateAccountView,
    UserLanguageListView,
    UserLanguageDetailView,


    FriendshipListView,
    FriendshipIncomingView,
    FriendshipActionView,
    FriendshipDeleteView,
    PublicAuthorProfileView,
)

app_name = 'users'

urlpatterns = [
    path('register',         RegisterView.as_view(),               name='register'),
    path('register/',        RegisterView.as_view()),
    path('verify-email',     VerifyEmailView.as_view(),            name='verify-email'),
    path('verify-email/',    VerifyEmailView.as_view()),
    path('resend-verification',   ResendVerificationCodeView.as_view(), name='resend-verification'),
    path('resend-verification/',  ResendVerificationCodeView.as_view()),
    path('login',            LoginView.as_view(),                  name='login'),
    path('login/',           LoginView.as_view()),
    path('token/refresh',    TokenRefreshView.as_view(),           name='token-refresh'),
    path('token/refresh/',   TokenRefreshView.as_view()),
    path('logout',           LogoutView.as_view(),                 name='logout'),
    path('logout/',          LogoutView.as_view()),
    path('change-password',  ChangePasswordView.as_view(),         name='change-password'),
    path('change-password/', ChangePasswordView.as_view()),

    path('me',                MeView.as_view(),                    name='me'),
    path('me/',               MeView.as_view()),
    path('me/profile',        UpdateProfileView.as_view(),         name='update-profile'),
    path('me/profile/',       UpdateProfileView.as_view()),
    path('me/account',        UpdateAccountView.as_view(),         name='update-account'),
    path('me/account/',       UpdateAccountView.as_view()),
    path('me/languages',      UserLanguageListView.as_view(),      name='user-languages'),
    path('me/languages/',     UserLanguageListView.as_view()),
    path('me/languages/<uuid:pk>',    UserLanguageDetailView.as_view(), name='user-language-detail'),
    path('me/languages/<uuid:pk>/',   UserLanguageDetailView.as_view()),

    path('friends',                       FriendshipListView.as_view(),     name='friends'),
    path('friends/',                      FriendshipListView.as_view()),
    path('friends/incoming',              FriendshipIncomingView.as_view(), name='friends-incoming'),
    path('friends/incoming/',             FriendshipIncomingView.as_view()),
    path('friends/<uuid:pk>/action',      FriendshipActionView.as_view(),  name='friend-action'),
    path('friends/<uuid:pk>/action/',     FriendshipActionView.as_view()),
    path('friends/<uuid:pk>/delete',      FriendshipDeleteView.as_view(),  name='friend-delete'),
    path('friends/<uuid:pk>/delete/',     FriendshipDeleteView.as_view()),
    path('<str:username>',                PublicAuthorProfileView.as_view(), name='public-profile'),
    path('<str:username>/',               PublicAuthorProfileView.as_view()),
]