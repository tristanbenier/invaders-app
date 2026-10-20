from django.urls import path

from . import views

urlpatterns = [
    path("auth/csrf/", views.CsrfView.as_view(), name="auth-csrf"),
    path("auth/login/", views.LoginView.as_view(), name="auth-login"),
    path("auth/logout/", views.LogoutView.as_view(), name="auth-logout"),
    path("auth/me/", views.MeView.as_view(), name="auth-me"),
    path("auth/invitations/<str:token>/", views.PublicInvitationView.as_view(), name="auth-invitation"),
    path("auth/accept-invitation/", views.AcceptInvitationView.as_view(), name="auth-accept-invitation"),
    path("team/", views.TeamView.as_view(), name="team"),
    path("team/members/<int:pk>/", views.TeamMemberRemoveView.as_view(), name="team-member-remove"),
    path("invitations/", views.InvitationListCreateView.as_view(), name="invitations"),
    path("invitations/<int:pk>/", views.InvitationRevokeView.as_view(), name="invitation-revoke"),
]
