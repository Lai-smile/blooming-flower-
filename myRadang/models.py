from django.db import models

class RadangInfo(models.Model):
    username=models.CharField(max_length=20)
    sex=models.BooleanField(default=False)
    cardid=models.CharField(max_length=18)
    tall=models.DecimalField(max_digits=6,decimal_places=2)
    weight=models.DecimalField(max_digits=6,decimal_places=2)
    smoke = models.BooleanField(default=True)
    drink= models.BooleanField(default=True)
    ill = models.BooleanField(default=False) #是否父母兄弟患过此病症
    HP_infection=models.BooleanField(default=False) #是否幽门螺杆菌感染
    irregular_life=models.BooleanField(default=False) #是否长期不规律生活
    environment_change=models.BooleanField(default=False) #是否大地物理变化导致（气候变化，环境变化）
    Organ_change=models.BooleanField(default=False) #是否其他脏器病变导致
