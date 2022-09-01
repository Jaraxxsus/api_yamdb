
from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action, api_view
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework.permissions import (IsAdminUser,
                                        IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet


from api.permissions import (IsAdmin,
                             IsAdminOrReadOnly,
                             IsAuthorModeratorAdminOrReadOnly)
from api.serializers import (
    UserSerializer,
    CategorySerializer,
    GenreSerializer,
    TitlesSerializer,
    ReviewSerializer,
    CommentSerializer
)

from api.filters import TitlesFilter

from reviews.models import User, Category, Genre, Title, Review
from django.contrib.auth.tokens import default_token_generator
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from api.serializers import (SignUpSerializer, TokenSerializer)
from api.utils import send_mail_function


@api_view(["POST"])
def register_user(request):
    """Регистрация нового пользователя """
    serializer = SignUpSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    user = serializer.instance
    confirmation_code = default_token_generator.make_token(user)
    send_mail_function(user, confirmation_code)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["POST"])
def get_token_for_users(request):
    """Получить токен"""
    serializer = TokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.get_user()
    refresh = RefreshToken.for_user(user)
    return Response(
        {'refresh': str(refresh)},
        status=status.HTTP_200_OK)


class UserViewSet(ModelViewSet):
    """Логика работы с пользователями"""
    queryset = User.objects.all()
    filter_backends = (SearchFilter,)
    search_fields = ("username",)
    lookup_field = "username"
    permission_classes = (IsAdmin,)
    serializer_class = UserSerializer
    @action(
        methods=["GET", "PATCH"],
        permission_classes=(IsAuthenticated,),
        url_path="me", detail=False)
    def users_profile(self, request):
        if request.method == "PATCH":
            serializer = self.serializer_class(
                request.user,
                data=request.data,
                partial=True)
            serializer.is_valid(raise_exception=True)
            if request.user.role == "user":
                serializer.validated_data["role"] = "user"
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_200_OK)
        # Если GET запрос, возвращаем страницу пользователя
        serializer = self.serializer_class(request.user)
        return Response(
            serializer.data, status=status.HTTP_200_OK)


class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = (SearchFilter,)
    search_fields = ("name",)
    lookup_field = "slug"
    permission_classes = (IsAdminOrReadOnly,)

    def retrieve(self, request, *args, **kwargs):
        raise MethodNotAllowed('GET')

    def update(self, request, *args, **kwargs):
        raise MethodNotAllowed('PATCH')


class GenreViewSet(ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    filter_backends = (SearchFilter,)
    search_fields = ("name",)
    lookup_field = "slug"
    permission_classes = (IsAdminOrReadOnly,)

    def retrieve(self, request, *args, **kwargs):
        raise MethodNotAllowed('GET')

    def update(self, request, *args, **kwargs):
        raise MethodNotAllowed('PATCH')


class TitlesViewSet(ModelViewSet):
    queryset = Title.objects.all()
    serializer_class = TitlesSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TitlesFilter
    permission_classes = (IsAdminOrReadOnly,)


class ReviewViewSet(ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [
        IsAuthorModeratorAdminOrReadOnly,
        IsAuthenticatedOrReadOnly
    ]

    def get_queryset(self):
        title = get_object_or_404(Title, id=self.kwargs['title_id'])
        return title.reviews.all()

    def perform_create(self, serializer):
        title = get_object_or_404(Title, id=self.kwargs['title_id'])
        serializer.save(author=self.request.user, title=title)


class CommentViewSet(ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [
        IsAuthorModeratorAdminOrReadOnly,
        IsAuthenticatedOrReadOnly
    ]

    def get_queryset(self):
        review = get_object_or_404(
            Review, id=self.kwargs['review_id'],
            title__id=self.kwargs['title_id']
        )
        return review.comments.all()

    def perform_create(self, serializer):
        review = get_object_or_404(
            Review, id=self.kwargs['review_id'],
            title__id=self.kwargs['title_id']
        )

        serializer.save(author=self.request.user, review=review)



