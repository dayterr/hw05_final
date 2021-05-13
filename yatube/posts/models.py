from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField(verbose_name='Название соообщества',
                             max_length=200)
    slug = models.SlugField(verbose_name='Адрес сообщества', unique=True)
    description = models.TextField(verbose_name='Описание сообщества')

    class Meta:
        verbose_name = 'Сообщество'
        verbose_name_plural = 'Сообщества'

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(verbose_name='Текст поста')
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)
    author = models.ForeignKey(User, verbose_name='Автор поста',
                               on_delete=models.CASCADE,
                               related_name='posts',
                               null=True,)
    group = models.ForeignKey(Group, verbose_name='Сообщество',
                              on_delete=models.SET_NULL,
                              blank=True, null=True,
                              related_name='posts')
    image = models.ImageField(upload_to='posts/', blank=True, null=True)

    class Meta:
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):
    post = models.ForeignKey(Post, verbose_name='Пост',
                             on_delete=models.CASCADE,
                             related_name='comments')
    author = models.ForeignKey(User, verbose_name='Автор комментария',
                               on_delete=models.CASCADE,
                               related_name='comments')
    text = models.TextField(verbose_name='Текст комментария')
    created = models.DateTimeField(verbose_name='Дата публикации',
                                   auto_now_add=True)


class Follow(models.Model):
    user = models.ForeignKey(User, verbose_name='Подписчик',
                             related_name='follower',
                             on_delete=models.CASCADE)
    author = models.ForeignKey(User, verbose_name='Подписант',
                               related_name='following',
                               on_delete=models.CASCADE)
