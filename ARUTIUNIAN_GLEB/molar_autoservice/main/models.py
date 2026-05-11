from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class Role(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=100)

    class Meta:
        db_table = 'roles'
        managed = False

    def __str__(self):
        return self.title
    
class User(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    surname = models.CharField(max_length=50)
    email = models.CharField(max_length=100, unique=True)
    hash_passwd = models.TextField()

    role_id = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        db_column='role_id'
    )

    class Meta:
        db_table = 'users'
        managed = False

    def set_password(self, raw_password):
        self.hash_passwd = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.hash_passwd)

    @property
    def role_name(self):
        return self.role_id.name
    
    @property
    def is_authenticated(self):
        return True


class Client(models.Model):
    user_id = models.OneToOneField(User, on_delete=models.CASCADE, db_column='user_id', primary_key=True)
    phone = models.CharField(max_length=20)
    type_client_id = models.IntegerField(null=True, blank=True)
    
    class Meta:
        db_table = 'client'
        managed = False


class Car(models.Model):
    id = models.AutoField(primary_key=True)
    client_id = models.IntegerField()
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    vin = models.CharField(max_length=50, null=True, blank=True)
    plate_number = models.CharField(max_length=20)
    year_produced = models.IntegerField(null=True, blank=True)
    color = models.CharField(max_length=50, null=True, blank=True)
    
    class Meta:
        db_table = 'cars'
        managed = False
    
    def __str__(self):
        return f"{self.brand} {self.model} ({self.plate_number})"


class Order(models.Model):
    id = models.AutoField(primary_key=True)
    status_id = models.IntegerField(null=True, blank=True)
    payment_id = models.IntegerField(null=True, blank=True)
    problem_desc = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    car_id = models.ForeignKey(
        Car,
        on_delete=models.CASCADE,
        db_column='car_id'
    )

    client_id = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        db_column='client_id'
    )

    class Meta:
        db_table = 'orders'
        managed = False
        
    
class Manager(models.Model):
    user_id = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        db_column='user_id',
        primary_key=True
    )
    work_phone = models.CharField(max_length=30, blank=True, null=True)

    class Meta:
        db_table = 'manager'
        managed = False


class Master(models.Model):
    user_id = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        db_column='user_id',
        primary_key=True
    )
    qualify_id = models.IntegerField(null=True, blank=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    is_admin = models.BooleanField(default=False)

    class Meta:
        db_table = 'master'
        managed = False
    
class ScheduleShift(models.Model):
    id = models.AutoField(primary_key=True)

    employee = models.ForeignKey(
        Master,
        on_delete=models.CASCADE,
        db_column='employee_id'
    )

    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=20, default='draft')

    class Meta:
        db_table = 'schedule_shifts'
        managed = False