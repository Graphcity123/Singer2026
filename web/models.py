from django.db import models

# Create your models here.

class Singer(models.Model):
    id=models.IntegerField(primary_key=True,verbose_name="歌手ID")
    name=models.CharField(max_length=200,verbose_name="歌手姓名")
    image_url=models.CharField(max_length=200,verbose_name="歌手图片地址")
    desc=models.TextField(blank=True,null=True,default="",verbose_name="歌手简介")
    source_url=models.URLField(max_length=200,verbose_name="歌手原始链接")

class Song(models.Model):
    id=models.IntegerField(primary_key=True,verbose_name="歌曲ID")
    name=models.CharField(max_length=200,verbose_name="歌曲名")
    image_url=models.CharField(max_length=200,verbose_name="歌曲图片地址")
    source_url=models.URLField(max_length=200,verbose_name="歌曲原始链接")
    lyrics=models.TextField(blank=True,null=True,default="",verbose_name="歌曲歌词")
    singers=models.ManyToManyField(Singer,related_name="songs")

class Comment(models.Model):
    name=models.CharField(max_length=200,verbose_name="昵称")
    content=models.TextField(blank=True,null=True,default="",verbose_name="评论内容")
    song=models.ForeignKey(Song,related_name="comments",on_delete=models.CASCADE)
    create_time=models.DateField(verbose_name="创建日期")