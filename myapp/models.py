from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    email = models.EmailField(unique=True)
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(unique=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    twilio_sid = models.CharField(max_length=34, blank=True, null=True)
    twilio_token = models.CharField(max_length=32, blank=True, null=True)
    twilio_number = models.CharField(max_length=15, blank=True, null=True)
    your_number = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return self.name or self.user.username

class Traveler(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')])
    travel_class = models.CharField(max_length=20, choices=[('economy', 'Economy'), ('business', 'Business'), ('first-class', 'First Class')])
    mobile = models.CharField(max_length=10, blank=True, null=True)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name

class Luggage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_weight = models.PositiveIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Luggage for {self.user.username}"

class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ticket_number = models.CharField(max_length=12, unique=True)
    flight_id = models.CharField(max_length=100, blank=True, null=True)
    flight_details = models.TextField()
    outbound_id = models.CharField(max_length=20, blank=True, null=True)
    return_id = models.CharField(max_length=20, blank=True, null=True)
    car_service_destination = models.BooleanField(default=False)
    car_service_return = models.BooleanField(default=False)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking {self.ticket_number} for {self.user.username}"

class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    flight_id = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[('completed', 'Completed'), ('pending', 'Pending'), ('failed', 'Failed')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for {self.flight_id} by {self.user.username}"

class Notification(models.Model):
    recipient = models.CharField(max_length=100)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification to {self.recipient}: {self.message[:50]}"

class FlightDelay(models.Model):
    flight_number = models.CharField(max_length=20)  # Changed from flight_id to flight_number
    reason = models.TextField()
    delay_duration = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Delay for {self.flight_number}"

class UserQuery(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    query_id = models.CharField(max_length=36, unique=True)  # Increased max_length to 36 to accommodate UUID
    query_text = models.TextField()
    submission_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[('open', 'Open'), ('resolved', 'Resolved')], default='open')

    def __str__(self):
        return f"Query {self.query_id} by {self.user.username}"