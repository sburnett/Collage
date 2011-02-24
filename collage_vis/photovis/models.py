from django.db import models 

class Stories(models.Model):
    class Meta:
        db_table = 'stories'

    rowid = models.AutoField(primary_key=True, db_column='ROWID')
    story = models.TextField()
    state = models.CharField(max_length=16)

class PhotosQueued(models.Model):
    class Meta:
        db_table = 'photos_queued'

    rowid = models.AutoField(primary_key=True, db_column='ROWID')
    identifier = models.TextField()
    thumbnail = models.TextField()

class PhotosEmbedding(models.Model):
    class Meta:
        db_table = 'photos_embedding'

    rowid = models.AutoField(primary_key=True, db_column='ROWID')
    identifier = models.TextField()
    thumbnail = models.TextField()

class PhotosUploaded(models.Model):
    class Meta:
        db_table = 'photos_uploaded'

    rowid = models.AutoField(primary_key=True, db_column='ROWID')
    identifier = models.TextField()
    thumbnail = models.TextField()
