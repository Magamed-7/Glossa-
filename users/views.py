import random
import logging
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

from .models import Profile, EmailVerification, Friendship, UserLanguage
from .serializers import (
    UserRegisterSerializer,
    EmailVerificationSerializer,
    UserProfileSerializer,
    ProfileSerializer,
    UserLanguageSerializer,
    FriendshipSerializer,
    PublicAuthorProfileSerializer,
)

User = get_user_model()
logger = logging.getLogger('users')




class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()

        
        code = str(random.randint(100000, 999999))
        EmailVerification.objects.create(
            user=user,
            code=code,
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        # TODO
        logger.info(f'[DEV] Код верификации для {user.email}: {code}')

        logger.info(f'Новый пользователь зарегистрирован: {user.email}')
        return Response(
            {'detail': 'Регистрация успешна. Проверьте email для подтверждения аккаунта.'},
            status=status.HTTP_201_CREATED,
        )


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        code = serializer.validated_data['code']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'detail': 'Пользователь не найден.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        verification = (
            EmailVerification.objects
            .filter(user=user, code=code, is_used=False)
            .order_by('-created_at')
            .first()
        )

        if not verification:
            return Response(
                {'detail': 'Неверный код подтверждения.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if verification.is_expired:
            return Response(
                {'detail': 'Срок действия кода истёк. Запросите новый код.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        
        verification.is_used = True
        verification.save()
        user.is_verified = True
        user.save()

        logger.info(f'Email подтверждён: {user.email}')

        # TODO
        return Response(
            {'detail': 'Email успешно подтверждён. Аккаунт активирован.'},
            status=status.HTTP_200_OK,
        )


class ResendVerificationCodeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response(
                {'detail': 'Email обязателен.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'detail': 'Если аккаунт существует, код будет отправлен.'},
                status=status.HTTP_200_OK,
            )

        if user.is_verified:
            return Response(
                {'detail': 'Аккаунт уже подтверждён.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

    
        EmailVerification.objects.filter(user=user, is_used=False).update(is_used=True)

        
        code = str(random.randint(100000, 999999))
        EmailVerification.objects.create(
            user=user,
            code=code,
            expires_at=timezone.now() + timedelta(minutes=10),
        )

        # TODO
        logger.info(f'[DEV] Новый код верификации для {user.email}: {code}')

        return Response(
            {'detail': 'Если аккаунт существует, код будет отправлен.'},
            status=status.HTTP_200_OK,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {'detail': 'Email и пароль обязательны.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'detail': 'Неверный email или пароль.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.check_password(password):
            return Response(
                {'detail': 'Неверный email или пароль.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return Response(
                {'detail': 'Аккаунт заблокирован. Обратитесь в поддержку.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not user.is_verified:
            return Response(
                {'detail': 'Аккаунт не подтверждён. Проверьте email для верификации.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])

        refresh = RefreshToken.for_user(user)
        logger.info(f'Пользователь вошёл: {user.email}')

        return Response(
            {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'id': str(user.id),
                    'username': user.username,
                    'email': user.email,
                    'is_verified': user.is_verified,
                    'dashboard_role': user.dashboard_role,
                },
            },
            status=status.HTTP_200_OK,
        )


class TokenRefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'detail': 'Refresh токен обязателен.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            refresh = RefreshToken(refresh_token)
            data = {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
            return Response(data, status=status.HTTP_200_OK)
        except Exception:
            return Response(
                {'detail': 'Токен недействителен или истёк.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'detail': 'Refresh токен обязателен.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            logger.info(f'Пользователь вышел: {request.user.email}')
            return Response({'detail': 'Выход выполнен успешно.'}, status=status.HTTP_200_OK)
        except Exception:
            return Response(
                {'detail': 'Токен недействителен или уже инвалидирован.'},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not old_password or not new_password:
            return Response(
                {'detail': 'Старый и новый пароли обязательны.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not request.user.check_password(old_password):
            return Response(
                {'detail': 'Неверный текущий пароль.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(new_password) < 8:
            return Response(
                {'detail': 'Новый пароль должен содержать не менее 8 символов.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.user.set_password(new_password)
        request.user.save()


        outstanding_tokens = OutstandingToken.objects.filter(user=request.user)
        for token in outstanding_tokens:
            BlacklistedToken.objects.get_or_create(token=token)

        logger.info(f'Пароль изменён: {request.user.email}')
        return Response(
            {'detail': 'Пароль успешно изменён. Войдите заново.'},
            status=status.HTTP_200_OK,
        )
    






class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UpdateProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        logger.info(f'Профиль обновлён: {request.user.email}')
        return Response(serializer.data, status=status.HTTP_200_OK)


class UpdateAccountView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        user = request.user
        allowed_fields = ['email', 'phone', 'push_enabled', 'push_token']
        data = {k: v for k, v in request.data.items() if k in allowed_fields}

        new_email = data.get('email')
        if new_email and new_email != user.email:
            
            if User.objects.filter(email=new_email).exclude(id=user.id).exists():
                return Response(
                    {'detail': 'Этот email уже используется.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user.email = new_email
            user.is_verified = False

            
            code = str(random.randint(100000, 999999))
            EmailVerification.objects.create(
                user=user,
                code=code,
                expires_at=timezone.now() + timedelta(minutes=10),
            )
            # TODO
            logger.info(f'[DEV] Код верификации нового email {new_email}: {code}')

        if 'phone' in data:
            user.phone = data['phone']
        if 'push_enabled' in data:
            user.push_enabled = data['push_enabled']
        if 'push_token' in data:
            user.push_token = data['push_token']

        user.save()
        logger.info(f'Аккаунт обновлён: {user.email}')
        return Response({'detail': 'Аккаунт обновлён.'}, status=status.HTTP_200_OK)


class UserLanguageListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        languages = UserLanguage.objects.filter(user=request.user)
        serializer = UserLanguageSerializer(languages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = UserLanguageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        language_code = serializer.validated_data['language_code']
        if UserLanguage.objects.filter(user=request.user, language_code=language_code).exists():
            return Response(
                {'detail': 'Этот язык уже добавлен в ваш список.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer.save(user=request.user)
        logger.info(f'Добавлен язык {language_code} для: {request.user.email}')
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UserLanguageDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_language(self, request, pk):
        try:
            return UserLanguage.objects.get(id=pk, user=request.user)
        except UserLanguage.DoesNotExist:
            return None

    def patch(self, request, pk):
        language = self._get_language(request, pk)
        if not language:
            return Response({'detail': 'Язык не найден.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserLanguageSerializer(language, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        language = self._get_language(request, pk)
        if not language:
            return Response({'detail': 'Язык не найден.'}, status=status.HTTP_404_NOT_FOUND)

        language.delete()
        logger.info(f'Язык {language.language_code} удалён для: {request.user.email}')
        return Response(status=status.HTTP_204_NO_CONTENT)








class PublicAuthorProfileView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, username):
        try:
            user = User.objects.select_related('profile').prefetch_related(
                'user_languages',
                'user_achievements',
            ).get(username=username, is_active=True)
        except User.DoesNotExist:
            return Response({'detail': 'Пользователь не найден.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = PublicAuthorProfileSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class FriendshipListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        friendships = Friendship.objects.filter(
            from_user=request.user,
            status='accepted',
        ).select_related('to_user') | Friendship.objects.filter(
            to_user=request.user,
            status='accepted',
        ).select_related('from_user')

        serializer = FriendshipSerializer(friendships, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        to_username = request.data.get('to_user')
        if not to_username:
            return Response(
                {'detail': 'Имя пользователя (to_user) обязательно.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            to_user = User.objects.get(username=to_username)
        except User.DoesNotExist:
            return Response({'detail': 'Пользователь не найден.'}, status=status.HTTP_404_NOT_FOUND)

        if to_user == request.user:
            return Response(
                {'detail': 'Нельзя отправить запрос самому себе.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if Friendship.objects.filter(from_user=request.user, to_user=to_user).exists():
            return Response(
                {'detail': 'Запрос уже отправлен или вы уже друзья.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        friendship = Friendship.objects.create(
            from_user=request.user,
            to_user=to_user,
            status='pending',
        )


        logger.info(f'Запрос в друзья: {request.user.username} -> {to_user.username}')
        serializer = FriendshipSerializer(friendship)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class FriendshipIncomingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        incoming = Friendship.objects.filter(
            to_user=request.user,
            status='pending',
        ).select_related('from_user')
        serializer = FriendshipSerializer(incoming, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class FriendshipActionView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            friendship = Friendship.objects.get(id=pk, to_user=request.user, status='pending')
        except Friendship.DoesNotExist:
            return Response(
                {'detail': 'Запрос в друзья не найден.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        action = request.data.get('action')
        if action not in ['accept', 'reject']:
            return Response(
                {'detail': 'Действие должно быть "accept" или "reject".'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if action == 'accept':
            friendship.status = 'accepted'
            # TODO
            logger.info(f'Дружба принята: {friendship.from_user.username} <-> {request.user.username}')
        else:
            friendship.status = 'rejected'
            logger.info(f'Дружба отклонена: {friendship.from_user.username} -> {request.user.username}')

        friendship.save()
        serializer = FriendshipSerializer(friendship)
        return Response(serializer.data, status=status.HTTP_200_OK)


class FriendshipDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            friendship = Friendship.objects.get(
                id=pk,
                status='accepted',
            )
           
            if friendship.from_user != request.user and friendship.to_user != request.user:
                return Response(status=status.HTTP_403_FORBIDDEN)
        except Friendship.DoesNotExist:
            return Response({'detail': 'Дружба не найдена.'}, status=status.HTTP_404_NOT_FOUND)

        friendship.delete()
        logger.info(f'Дружба удалена пользователем: {request.user.username}')
        return Response(status=status.HTTP_204_NO_CONTENT)
