from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import render, redirect
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import MyUser
from accounts.permissions import IsUserOwner
from accounts.serializers import MyUserSerializer
from core.mixins import ViewSetPermissionByMethodMixin


# Create your views here.
class MyUserViewSet(
    ViewSetPermissionByMethodMixin, mixins.UpdateModelMixin, GenericViewSet
):
    serializer_class = MyUserSerializer
    queryset = MyUser.objects.filter(is_superuser=False, is_active=True).all()
    permission_classes = [IsAuthenticated]
    permission_action_classes = dict(
        create=(AllowAny,),
        retrieve=(IsUserOwner,),
        update=(IsUserOwner,),
        partial_update=(IsUserOwner,),
        login=(AllowAny,),
        leaderboard=(AllowAny,),
    )

    @action(detail=False, methods=["POST"])
    def login(self, request, *args, **kwargs):
        body = request.data

        if "username" not in body:
            message = ""
            if "username" not in body:
                message += "Username not found in request. "
            return Response({"message": message}, status=status.HTTP_400_BAD_REQUEST)

        username = body["username"]
        password = body["password"]

        existing_users = MyUser.objects.filter(username=username)

        user = None

        if existing_users.exists():
            user = existing_users.first()
            if not user.is_active:
                return Response(
                    {"message": "User inactive."}, status=status.HTTP_403_FORBIDDEN
                )
            else:
                is_correct = user.check_password(password)
                if is_correct:
                    refresh_token_obj = RefreshToken.for_user(user)
                    refresh_token = str(refresh_token_obj)
                    access_token = str(refresh_token_obj.access_token)
                    data = {
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                    }
                    return Response(data, status=status.HTTP_200_OK)
                else:
                    return Response(
                        {"message": "Unauthorized."},
                        status=status.HTTP_401_UNAUTHORIZED,
                    )
        else:
            user_serializer = self.serializer_class(data=body)
            if user_serializer.is_valid(raise_exception=True):
                user = user_serializer.save()

        if user:
            refresh_token_obj = RefreshToken.for_user(user)
            refresh_token = str(refresh_token_obj)
            access_token = str(refresh_token_obj.access_token)
            data = {"access_token": access_token, "refresh_token": refresh_token}
            return Response(data, status=status.HTTP_200_OK)

        else:
            Response({"message": "Bad request."}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["GET"])
    def my(self, request, *args, **kwargs):
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


def LogoutView(request):
    logout(request)
    return redirect("login_redirects")


def forgot_password(request):
    if request.method == "POST":
        username = request.POST.get("username")
        try:
            user = MyUser.objects.get(username=username)
            # TODO: TEMPLATE FORGOT PASS FLOW
        except MyUser.DoesNotExist:
            pass
        messages.add_message(
            request,
            messages.SUCCESS,
            "We have contacted you with further actions!",
        )
        return redirect("login")
    return render(request, "registration/forgot_password.html")
