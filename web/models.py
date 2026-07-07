from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Singer(models.Model):
    id=models.IntegerField(primary_key=True,verbose_name="歌手ID")
    name=models.CharField(max_length=200,verbose_name="歌手姓名")
    image_url=models.CharField(max_length=200,verbose_name="歌手图片地址")
    desc=models.TextField(blank=True,null=True,default="",verbose_name="歌手简介")
    source_url=models.URLField(max_length=200,verbose_name="歌手原始链接")
    sort_order=models.IntegerField(default=0,verbose_name="排序")

class Song(models.Model):
    id=models.IntegerField(primary_key=True,verbose_name="歌曲ID")
    name=models.CharField(max_length=200,verbose_name="歌曲名")
    image_url=models.CharField(max_length=200,verbose_name="歌曲图片地址")
    source_url=models.URLField(max_length=200,verbose_name="歌曲原始链接")
    lyrics=models.TextField(blank=True,null=True,default="",verbose_name="歌曲歌词")
    singers=models.ManyToManyField(Singer,related_name="songs")
    sort_order=models.IntegerField(default=0,verbose_name="排序")

class Comment(models.Model):
    user=models.ForeignKey(User,null=True,blank=True,on_delete=models.SET_NULL,verbose_name="用户")
    name=models.CharField(max_length=200,verbose_name="昵称")
    content=models.TextField(blank=True,null=True,default="",verbose_name="评论内容")
    song=models.ForeignKey(Song,related_name="comments",on_delete=models.CASCADE)
    create_time=models.DateField(verbose_name="创建日期")
    like_count=models.IntegerField(default=0,verbose_name="点赞数")


class CommentLike(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    comment=models.ForeignKey(Comment,on_delete=models.CASCADE,related_name="likes")

    class Meta:
        unique_together=('user','comment')


class FavoriteSong(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    song=models.ForeignKey(Song,on_delete=models.CASCADE,related_name="favorited_by")
    created_at=models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together=('user','song')


class UserProfile(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE,related_name="profile")
    avatar=models.ImageField(upload_to="avatars/",blank=True,null=True,verbose_name="头像")
    bio=models.TextField(blank=True,null=True,default="",verbose_name="个人简介")

    def __str__(self):
        return self.user.username


class FavoriteSinger(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    singer=models.ForeignKey(Singer,on_delete=models.CASCADE,related_name="favorited_by")
    created_at=models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together=('user','singer')