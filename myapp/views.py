from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from .models import User, Traveler, Luggage, Booking, UserProfile, Payment, Notification, FlightDelay, UserQuery
from django.http import JsonResponse
import uuid
import random
import string
from django import forms
from django.contrib.auth import authenticate, login, logout
from twilio.rest import Client
from django.views.decorators.csrf import csrf_exempt
import json
import logging
import time
from django.db import models
from django.db import IntegrityError
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)

# Custom User Creation Form
class CustomUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('username', 'email')

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

# Views for User Functionality
def logout_view(request):
    logout(request)
    return redirect('signin')


@login_required
def flight_booking(request):
    if request.method == 'POST':
        logger.info("POST data received: %s", request.POST)
        traveler_count = int(request.POST.get('traveler_count', 0))
        logger.info("Traveler Count: %d", traveler_count)

        if traveler_count == 0:
            messages.error(request, "Please add at least one traveler.")
            return render(request, 'myapp/User/t1.html')

        for i in range(1, traveler_count + 1):
            full_name = request.POST.get(f'name{i}')
            age = request.POST.get(f'age{i}')
            gender = request.POST.get(f'gender{i}')
            travel_class = request.POST.get(f'class{i}')
            mobile = request.POST.get(f'mobile{i}')
            email = request.POST.get(f'email{i}')
            logger.debug("Traveler %d: %s, %s, %s, %s, %s, %s", i, full_name, age, gender, travel_class, mobile, email)

            if all([full_name, age, gender, travel_class, mobile, email]):
                try:
                    Traveler.objects.create(
                        user=request.user,
                        full_name=full_name,
                        age=int(age),
                        gender=gender,
                        travel_class=travel_class,
                        mobile=mobile,
                        email=email
                    )
                    logger.info("Traveler %d saved successfully", i)
                except Exception as e:
                    logger.error("Error saving Traveler %d: %s", i, str(e))
                    messages.error(request, f"Error saving Traveler {i}: {str(e)}")
                    return render(request, 'myapp/User/t1.html')
            else:
                messages.error(request, f"Please complete all fields for Traveler {i}.")
                return render(request, 'myapp/User/t1.html')

        luggage_weight = request.POST.get('luggage')
        logger.debug("Luggage Weight: %s", luggage_weight)
        if luggage_weight:
            try:
                Luggage.objects.create(
                    user=request.user,
                    total_weight=int(luggage_weight)
                )
                logger.info("Luggage saved successfully")
            except Exception as e:
                logger.error("Error saving Luggage: %s", str(e))
                messages.error(request, f"Error saving luggage: {str(e)}")
                return render(request, 'myapp/User/t1.html')

        messages.success(request, "Travel details saved successfully!")
        return redirect('home_2')

    return render(request, 'myapp/User/t1.html')

@login_required
def home_1(request):
    return render(request, 'myapp/User/home_1.html', {'user': request.user})

@login_required
def home_2(request):
    travelers = Traveler.objects.filter(user=request.user).order_by('-created_at')
    luggage = Luggage.objects.filter(user=request.user).order_by('-created_at').first()

    traveler_details = [
        {
            'full_name': traveler.full_name,
            'age': traveler.age,
            'gender': traveler.gender,
            'travel_class': traveler.travel_class,
            'mobile': traveler.mobile,
            'email': traveler.email,
            'category': "Kid" if traveler.age < 18 else "Adult" if traveler.age < 60 else "Senior Citizen",
        } for traveler in travelers
    ]

    total_passengers = travelers.count()

    context = {
        'travelers': traveler_details,
        'luggage': luggage.total_weight if luggage else 0,
        'total_passengers': total_passengers,
    }
    return render(request, 'myapp/User/home_2.html', context)

@login_required
def t1_view(request):
    return render(request, 'myapp/User/t1.html')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'name': user.username,
                    'email': user.email,
                }
            )
            logger.info("User %s registered and UserProfile created", user.username)
            return redirect('home_1')
    else:
        form = CustomUserCreationForm()
    return render(request, 'myapp/User/register.html', {'form': form})

def signin(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is None:
            logger.warning("Invalid login attempt for username: %s", username)
            return render(request, 'myapp/User/sign_in.html', {
                'error': 'Invalid user credentials',
                'username': username
            })

        login(request, user)
        logger.info("User %s logged in successfully as regular user", username)
        return redirect('home_1')

    return render(request, 'myapp/User/sign_in.html')

def admin_signin(request):
    if request.method == 'POST':
        admin_username = request.POST.get('admin_username')
        admin_password = request.POST.get('admin_password')

        admin_credentials = {
            'Gunaseelan': 'Guna@3975',
            'Jayasri': 'Jaya@1234',
            'Mahalingam': 'Maha@1234'
        }

        if not admin_username or not admin_password:
            logger.warning("Admin login attempted without credentials")
            return render(request, 'myapp/Admin/admin_signin.html', {
                'error': 'Admin username and password are required',
                'admin_username': admin_username
            })

        if admin_username not in admin_credentials or admin_password != admin_credentials[admin_username]:
            logger.warning("Invalid admin credentials for admin_username: %s", admin_username)
            return render(request, 'myapp/Admin/admin_signin.html', {
                'error': 'Invalid admin credentials',
                'admin_username': admin_username
            })

        try:
            user = User.objects.get(username=admin_username)
        except User.DoesNotExist:
            logger.info("Admin user %s does not exist, creating new user", admin_username)
            user = User.objects.create(
                username=admin_username,
                email=f"{admin_username.lower()}@example.com",
                is_staff=True,
                is_superuser=False
            )
            user.set_password(admin_password)
            user.save()
            logger.info("Admin user %s created successfully", admin_username)

        if not user.is_staff:
            user.is_staff = True
            user.save()
            logger.info("Updated user %s to be a staff member", admin_username)

        login(request, user)
        logger.info("Admin %s logged in successfully", admin_username)
        return redirect('admin_dashboard')

    return render(request, 'myapp/Admin/admin_signin.html')




@login_required
def search_flights(request):
    if request.method == 'GET':
        total_passengers = Traveler.objects.filter(user=request.user).count()
        if total_passengers < 1:
            messages.error(request, "Please add at least one traveler before searching for flights.")
            return redirect('t_1')

        departure = request.GET.get('departure')
        destination = request.GET.get('destination')
        date = request.GET.get('date')
        time = request.GET.get('time')
        return_date = request.GET.get('return_date')
        car_service_destination = request.GET.get('car_service_destination') == 'yes'
        car_service_return = request.GET.get('car_service_return') == 'yes'

        if not all([departure, destination, date, time]):
            messages.error(request, "Please fill in all required fields.")
            return redirect('home_2')

        if departure == destination:
            messages.error(request, "Departure and destination cities cannot be the same.")
            return redirect('home_2')

        if time not in ['morning', 'afternoon', 'evening']:
            messages.error(request, "Invalid time selection.")
            return redirect('home_2')

        travelers = Traveler.objects.filter(user=request.user).order_by('-created_at')
        luggage = Luggage.objects.filter(user=request.user).order_by('-created_at').first()

        traveler_details = [
            {'full_name': traveler.full_name, 'email': traveler.email} for traveler in travelers
        ]

        context = {
            'departure': departure,
            'destination': destination,
            'date': date,
            'time': time,
            'return_date': return_date,
            'car_service_destination': car_service_destination,
            'car_service_return': car_service_return,
            'travelers': traveler_details,
            'luggage': luggage.total_weight if luggage else 0,
            'total_passengers': total_passengers,
        }
        return render(request, 'myapp/User/flight_search.html', context)
    return redirect('home_2')

@login_required
def confirm_booking(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

    try:
        logger.info("Received POST data: %s", request.POST)

        outbound_flight = request.POST.get('outbound_flight', '')
        base_price = request.POST.get('base_price', '0')
        traveler_count = request.POST.get('traveler_count', '1')
        coupon = request.POST.get('coupon', '')
        email = request.POST.get('email', '')
        car_service_destination = request.POST.get('car_service_destination', 'false') == 'true'
        luggage = request.POST.get('luggage', '0')
        date = request.POST.get('date', '')
        return_flight = request.POST.get('return_flight', '')
        return_date = request.POST.get('return_date', '')
        car_service_return = request.POST.get('car_service_return', 'false') == 'true'

        try:
            base_price = float(base_price)
            traveler_count = int(traveler_count)
            luggage = int(luggage)
        except ValueError as e:
            logger.error("Invalid numeric data: base_price=%s, traveler_count=%s, luggage=%s, error=%s", base_price, traveler_count, luggage, str(e))
            return JsonResponse({'success': False, 'error': 'Invalid numeric data'}, status=400)

        outbound_json = request.POST.get('outbound', '{}')
        return_json = request.POST.get('return', '{}')
        outbound = {}
        return_trip = {}
        try:
            if outbound_json:
                outbound = json.loads(outbound_json)
            if return_json:
                return_trip = json.loads(return_json)
            outbound_base_price = float(outbound.get('basePrice', base_price))
            return_base_price = float(return_trip.get('basePrice', 0)) if return_flight else 0
            outbound_time = outbound.get('time', '7:01 PM - 10:06 PM').strip()
            return_time = return_trip.get('time', '').strip() if return_flight else ''
            logger.debug("Outbound time from JSON (stripped): %s", outbound_time)
            logger.debug("Return time from JSON (stripped): %s", return_time)
        except (json.JSONDecodeError, ValueError) as e:
            logger.error("JSON parsing or value error: %s, outbound_json=%s, return_json=%s", str(e), outbound_json, return_json)
            return JsonResponse({'success': False, 'error': 'Invalid flight data format'}, status=400)

        def calculate_duration(time_str):
            if not time_str or '-' not in time_str:
                logger.warning("Invalid time format or missing: %s", time_str)
                return 'N/A'
            try:
                time_str = time_str.replace(' ', '').replace('-', ' - ')
                start, end = [t.strip() for t in time_str.split(' - ')]
                def parse_time_component(time_component):
                    if 'PM' in time_component or 'AM' in time_component:
                        time_part = time_component.split(':')
                        hour = int(time_part[0])
                        minute_am_pm = time_part[1]
                        minute = int(minute_am_pm.replace('PM', '').replace('AM', ''))
                        pm = 'PM' in minute_am_pm
                        if pm and hour != 12:
                            hour += 12
                        elif pm and hour == 12:
                            hour = 12
                        elif not pm and hour == 12:
                            hour = 0
                        return hour, minute
                    else:
                        raise ValueError("AM/PM not found in time component")

                start_h, start_m = parse_time_component(start)
                end_h, end_m = parse_time_component(end)
                logger.debug("Parsed start: %d:%d, end: %d:%d", start_h, start_m, end_h, end_m)

                start_total = start_h * 60 + start_m
                end_total = end_h * 60 + end_m
                duration_mins = (end_total - start_total) % (24 * 60)
                if duration_mins > 12 * 60:
                    duration_mins = 24 * 60 - duration_mins
                hours = duration_mins // 60
                mins = duration_mins % 60
                result = f"{hours}h {mins}m"
                logger.debug("Calculated duration for %s: %s", time_str, result)
                return result
            except (ValueError, IndexError) as e:
                logger.error("Error calculating duration for %s: %s", time_str, str(e))
                return 'N/A'

        outbound_duration = calculate_duration(outbound_time)
        return_duration = calculate_duration(return_time) if return_flight else 'N/A'

        travelers = Traveler.objects.filter(user=request.user)
        if email not in [t.email for t in travelers]:
            return JsonResponse({'success': False, 'error': 'Invalid email'}, status=400)

        # Extract the actual flight numbers from outbound_flight and return_flight
        # Expected format: "Tokyo → Dubai, 6E-1442, 7:01 PM - 10:06 PM"
        outbound_id = 'N/A'
        return_id = ''
        if outbound_flight and outbound_flight != 'N/A':
            try:
                outbound_id = outbound_flight.split(', ')[1]  # Extract "6E-1442"
            except IndexError:
                logger.warning("Could not extract flight number from outbound_flight: %s", outbound_flight)
                outbound_id = 'N/A'

        if return_flight and return_flight != 'N/A':
            try:
                return_id = return_flight.split(', ')[1]  # Extract "6E-1573"
            except IndexError:
                logger.warning("Could not extract flight number from return_flight: %s", return_flight)
                return_id = ''

        # Ensure uniqueness of flight IDs in the database
        while Booking.objects.filter(outbound_id=outbound_id).exists():
            outbound_id = f"6E-{random.randint(1000, 9999)}"
        if return_id and Booking.objects.filter(return_id=return_id).exists():
            return_id = f"6E-{random.randint(1000, 9999)}"

        logger.debug("Outbound ID: %s", outbound_id)
        logger.debug("Return ID: %s", return_id)

        # Generate ticket ID in the format AD-QJP-95-6
        ticket_number = ''.join(random.choices(string.ascii_uppercase, k=2)) + '-' + \
                        ''.join(random.choices(string.ascii_uppercase, k=3)) + '-' + \
                        str(random.randint(10, 99)) + '-' + \
                        str(random.randint(0, 9))

        while Booking.objects.filter(ticket_number=ticket_number).exists():
            ticket_number = ''.join(random.choices(string.ascii_uppercase, k=2)) + '-' + \
                            ''.join(random.choices(string.ascii_uppercase, k=3)) + '-' + \
                            str(random.randint(10, 99)) + '-' + \
                            str(random.randint(0, 9))

        # Generate booking IDs in the format shown in thank_you.html (e.g., CK-KJE-95-8)
        def generate_booking_id():
            return ''.join(random.choices(string.ascii_uppercase, k=2)) + '-' + \
                   ''.join(random.choices(string.ascii_uppercase, k=3)) + '-' + \
                   str(random.randint(10, 99)) + '-' + \
                   str(random.randint(0, 9))

        outbound_booking_id = generate_booking_id()  # e.g., CK-KJE-95-8
        return_booking_id = generate_booking_id() if return_flight else ''  # e.g., MU-NPH-19-7

        CAR_SERVICE_SURCHARGE = 500
        outbound_cost = outbound_base_price + (CAR_SERVICE_SURCHARGE if car_service_destination else 0)
        return_cost = return_base_price + (CAR_SERVICE_SURCHARGE if car_service_return else 0) if return_flight else 0
        outbound_total = outbound_cost * traveler_count
        return_total = return_cost * traveler_count if return_flight else 0
        total_price = outbound_total + return_total

        discount = 0
        if coupon in {'FLIGHT10': 0.10, 'SAVE20': 0.20, 'WELCOME5': 0.05}:
            discount = {'FLIGHT10': 0.10, 'SAVE20': 0.20, 'WELCOME5': 0.05}[coupon]
            total_price *= (1 - discount)
            outbound_total *= (1 - discount)
            return_total *= (1 - discount) if return_flight else 0

        traveler_details = [
            {'full_name': t.full_name, 'email': t.email, 'mobile': t.mobile} for t in travelers
        ]

        # Store additional details in flight_details as a JSON string
        flight_details_dict = {
            'outbound_flight': outbound_flight,
            'outbound_id': outbound_id,
            'outbound_booking_id': outbound_booking_id,  # Store the booking ID
            'outbound_time': outbound_time,
            'outbound_duration': outbound_duration,
            'return_flight': return_flight,
            'return_id': return_id,
            'return_booking_id': return_booking_id,  # Store the return booking ID
            'return_time': return_time,
            'return_duration': return_duration,
            'date': date,
            'return_date': return_date,
            'travelers': traveler_details,
            'coupon': coupon,
            'payment_status': 'Pending'
        }
        flight_details_json = json.dumps(flight_details_dict)

        booking = Booking(
            user=request.user,
            ticket_number=ticket_number,
            flight_id=return_id if return_id else outbound_id,
            flight_details=flight_details_json,
            outbound_id=outbound_id,
            return_id=return_id,
            car_service_destination=car_service_destination,
            car_service_return=car_service_return,
            total_price=total_price,
            email=email,
        )
        booking.save()

        Payment.objects.create(
            user=request.user,
            flight_id=outbound_id,
            amount=outbound_total,
            status='completed'
        )
        logger.info("Payment recorded for outbound flight for user %s, flight_id: %s, amount: %s", request.user.username, outbound_id, outbound_total)

        if return_id:
            Payment.objects.create(
                user=request.user,
                flight_id=return_id,
                amount=return_total,
                status='completed'
            )
            logger.info("Payment recorded for return flight for user %s, flight_id: %s, amount: %s", request.user.username, return_id, return_total)

        request.session['booking_details'] = {
            'ticket_number': booking.ticket_number,
            'outbound_id': outbound_id,
            'outbound_booking_id': outbound_booking_id,  # Store in session
            'return_id': return_id,
            'return_booking_id': return_booking_id,  # Store in session
            'outbound_total_price': float(outbound_total),
            'return_total_price': float(return_total) if return_flight else 0,
            'total_price': float(total_price),
            'date': date,
            'return_date': return_date if return_flight else None,
            'outbound_duration': outbound_duration,
            'return_duration': return_duration if return_flight else 'N/A'
        }

        return JsonResponse({
            'success': True,
            'ticket_number': booking.ticket_number,
            'total_price': float(total_price)
        })
    except Exception as e:
        logger.error("Booking error: %s, POST data: %s", str(e), request.POST)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def thank_you(request):
    booking = Booking.objects.filter(user=request.user).order_by('-created_at').first()
    if not booking:
        messages.error(request, "No booking found. Please make a booking first.")
        return render(request, 'myapp/User/thank_you.html', {})

    try:
        flight_details = json.loads(booking.flight_details)
    except json.JSONDecodeError:
        flight_details = {}

    travelers = Traveler.objects.filter(user=request.user).order_by('-created_at')
    luggage = Luggage.objects.filter(user=request.user).order_by('-created_at').first()
    luggage_weight = luggage.total_weight if luggage else 0

    session_data = request.session.get('booking_details', {})
    outbound_duration = session_data.get('outbound_duration', flight_details.get('outbound_duration', 'N/A'))
    return_duration = session_data.get('return_duration', flight_details.get('return_duration', 'N/A'))

    def generate_random_ticket_number():
        while True:
            ticket_number = ''.join(random.choices(string.ascii_uppercase, k=2)) + '-' + \
                            ''.join(random.choices(string.ascii_uppercase, k=3)) + '-' + \
                            str(random.randint(10, 99)) + '-' + \
                            str(random.randint(0, 9))
            if not Booking.objects.filter(ticket_number=ticket_number).exists():
                return ticket_number

    outbound_ticket_number = generate_random_ticket_number()
    return_ticket_number = generate_random_ticket_number()

    # Extract the actual flight number from flight_details instead of using outbound_id
    outbound_flight_info = flight_details.get('outbound_flight', 'N/A')
    outbound_flight_number = 'N/A'
    if outbound_flight_info != 'N/A':
        # Expected format: "Tokyo → Dubai, 6E-1166, 7:01 PM - 10:06 PM"
        try:
            outbound_flight_number = outbound_flight_info.split(', ')[1]  # Extract "6E-1166"
        except IndexError:
            outbound_flight_number = 'N/A'

    outbound = {
        'ticket_number': outbound_ticket_number,
        'route': flight_details.get('outbound_flight', 'N/A').split(',')[0],
        'flight_number': outbound_flight_number,  # Use the extracted flight number
        'airline': 'Inido',
        'timing': flight_details.get('outbound_time', 'N/A'),
        'duration': outbound_duration,
        'date': session_data.get('date', flight_details.get('date', booking.created_at.strftime('%Y-%m-%d'))),
        'car_service': 'YES' if booking.car_service_destination else 'NO',
        'travelers': ", ".join([traveler.full_name for traveler in travelers]),
        'luggage': f"{luggage_weight} kg",
        'total_price': session_data.get('outbound_total_price', float(booking.total_price) / 2 if flight_details.get('return_flight') else float(booking.total_price)),
        'id': session_data.get('outbound_booking_id', flight_details.get('outbound_booking_id', 'CK-KJE-95-8')),
    }

    return_data = {}
    if flight_details.get('return_flight'):
        # Extract the actual return flight number from flight_details
        return_flight_info = flight_details.get('return_flight', 'N/A')
        return_flight_number = 'N/A'
        if return_flight_info != 'N/A':
            # Expected format: "Dubai → Tokyo, 6E-1167, 6:02 PM - 9:13 PM"
            try:
                return_flight_number = return_flight_info.split(', ')[1]  # Extract "6E-1167"
            except IndexError:
                return_flight_number = 'N/A'

        return_data = {
            'ticket_number': return_ticket_number,
            'route': flight_details.get('return_flight', 'N/A').split(',')[0],
            'flight_number': return_flight_number,  # Use the extracted flight number
            'airline': 'Inido',
            'timing': flight_details.get('return_time', 'N/A'),
            'duration': return_duration,
            'date': session_data.get('return_date', flight_details.get('return_date', 'N/A')),
            'car_service': 'YES' if booking.car_service_return else 'NO',
            'travelers': outbound['travelers'],
            'luggage': outbound['luggage'],
            'total_price': session_data.get('return_total_price', float(booking.total_price) / 2),
            'id': session_data.get('return_booking_id', flight_details.get('return_booking_id', 'MU-NPH-19-7')),
        }

    context = {
        'outbound': outbound,
        'return': return_data if return_data else None,
    }

    # Send booking confirmation email to the user
    try:
        # Construct the email body with booking details
        email_body = (
            "Dear Passenger,\n\n"
            "Thank you for booking with Inido Airlines. Your flight booking has been confirmed. Below are your ticket details:\n\n"
            "=== Outbound Ticket ===\n"
            f"Ticket Number: {outbound['ticket_number']}\n"
            f"Route: {outbound['route']}\n"
            f"Flight Number: {outbound['flight_number']}\n"
            f"Airline: {outbound['airline']}\n"
            f"Timing: {outbound['timing']}\n"
            f"Duration: {outbound['duration']}\n"
            f"Date: {outbound['date']}\n"
            f"Car Service: {outbound['car_service']}\n"
            f"Travellers: {outbound['travelers']}\n"
            f"Luggage: {outbound['luggage']}\n"
            f"Total Price: ₹{int(outbound['total_price'])}\n"
            f"Booking ID: {outbound['id']}\n"
        )

        if return_data:
            email_body += (
                "\n=== Return Ticket ===\n"
                f"Ticket Number: {return_data['ticket_number']}\n"
                f"Route: {return_data['route']}\n"
                f"Flight Number: {return_data['flight_number']}\n"
                f"Airline: {return_data['airline']}\n"
                f"Timing: {return_data['timing']}\n"
                f"Duration: {return_data['duration']}\n"
                f"Date: {return_data['date']}\n"
                f"Car Service: {return_data['car_service']}\n"
                f"Travellers: {return_data['travelers']}\n"
                f"Luggage: {return_data['luggage']}\n"
                f"Total Price: ₹{int(return_data['total_price'])}\n"
                f"Booking ID: {return_data['id']}\n"
            )

        email_body += (
            "\nWe look forward to serving you on board!\n\n"
            "Best regards,\nInido Airlines Team"
        )

        # Send the email
        send_mail(
            subject="Inido Airlines - Your Trafford Confirmation",
            message=email_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[booking.email],
            fail_silently=False,
        )
        logger.info(f"Booking confirmation email sent to {booking.email}")
    except Exception as e:
        logger.error(f"Failed to send booking confirmation email to {booking.email}: {str(e)}")
        messages.error(request, f"Failed to send booking confirmation email: {str(e)}")

    return render(request, 'myapp/User/thank_you.html', context)

@login_required
def configure_twilio(request):
    if request.method == 'POST':
        try:
            user_profile, created = UserProfile.objects.get_or_create(
                user=request.user,
                defaults={'name': request.user.username, 'email': request.user.email}
            )
            twilio_sid = request.POST.get('twilio_sid')
            twilio_token = request.POST.get('twilio_token')
            twilio_number = request.POST.get('twilio_number')
            your_number = request.POST.get('your_number')

            if not all([twilio_sid, twilio_token, twilio_number, your_number]):
                raise ValueError("One or more fields are empty")

            user_profile.twilio_sid = twilio_sid
            user_profile.twilio_token = twilio_token
            user_profile.twilio_number = twilio_number
            user_profile.your_number = your_number
            user_profile.save()
            logger.info("Twilio credentials updated for user %s", request.user.username)
            messages.success(request, "Twilio credentials configured successfully!")
            return redirect('home_1')
        except Exception as e:
            logger.error("Error configuring Twilio credentials: %s, POST data: %s", str(e), request.POST)
            messages.error(request, f"Failed to configure Twilio credentials: {str(e)}. Ensure all fields are filled.")
            return redirect('configure_twilio')
    user_profile, created = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={'name': request.user.username, 'email': request.user.email}
    )
    return render(request, 'myapp/User/configure_twilio.html', {
        'twilio_sid': user_profile.twilio_sid,
        'twilio_token': user_profile.twilio_token,
        'twilio_number': user_profile.twilio_number,
        'your_number': user_profile.your_number
    })

@login_required
def cancel_booking(request):
    if request.method == 'POST':
        flight_id = request.POST.get('flight_id')
        email = request.POST.get('email')
        try:
            booking = Booking.objects.filter(
                models.Q(outbound_id__iexact=flight_id) | models.Q(return_id__iexact=flight_id),
                email__iexact=email,
                user=request.user
            ).first()
            if not booking:
                return JsonResponse({'success': False, 'error': 'No booking found with the provided flight ID and email.'})
            booking.delete()
            logger.info("Booking cancelled successfully for flight_id: %s", flight_id)
            return JsonResponse({'success': True, 'message': 'Booking cancelled successfully!'})
        except Exception as e:
            logger.error("Error cancelling booking: %s", str(e))
            return JsonResponse({'success': False, 'error': str(e)})
    return render(request, 'myapp/User/cancel_booking.html')

@csrf_exempt
def send_otp(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_profile, created = UserProfile.objects.get_or_create(
                user=request.user,
                defaults={'name': request.user.username, 'email': request.user.email}
            )
            account_sid = data.get('sid', user_profile.twilio_sid)
            auth_token = data.get('token', user_profile.twilio_token)
            twilio_number = data.get('twilio_number', user_profile.twilio_number)
            your_number = data.get('your_number', user_profile.your_number)

            if not all([account_sid, auth_token, twilio_number, your_number]):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Missing required fields',
                    'details': {'sid': account_sid, 'token': auth_token, 'twilio_number': twilio_number, 'your_number': your_number}
                }, status=400)

            logger.info("Sending OTP to %s with SID: %s", your_number, account_sid)
            otp = random.randint(1000, 9999)
            request.session['otp'] = str(otp)
            request.session['otp_phone'] = your_number

            client = Client(account_sid, auth_token)
            message = client.messages.create(
                body=f"Hey! Welcome To Inido Airlines...Your OTP Is {otp}",
                from_=twilio_number,
                to=your_number
            )
            logger.info("Message sent successfully, SID: %s", message.sid)
            return JsonResponse({'status': 'success', 'message': 'OTP sent successfully', 'sid': message.sid})
        except Exception as e:
            logger.error("Error sending OTP: %s", str(e))
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@csrf_exempt
def verify_otp(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            entered_otp = data.get('otp')
            your_number = data.get('your_number')
            stored_otp = request.session.get('otp')
            stored_phone = request.session.get('otp_phone')

            logger.debug("Session OTP: %s, Session Phone: %s", stored_otp, stored_phone)
            logger.debug("Entered OTP: %s, Entered Phone: %s", entered_otp, your_number)

            if not entered_otp or not stored_otp or not stored_phone:
                return JsonResponse({'status': 'error', 'message': 'OTP or phone number missing'}, status=400)

            if your_number.strip() != stored_phone.strip():
                return JsonResponse({'status': 'error', 'message': 'Phone number does not match'}, status=400)

            if str(entered_otp) == stored_otp:
                logger.info("OTP verified successfully for phone: %s", your_number)
                request.session.pop('otp', None)
                request.session.pop('otp_phone', None)
                return JsonResponse({'status': "success", 'message': 'OTP verified successfully'})
            else:
                logger.warning("Invalid OTP entered: %s for phone: %s", entered_otp, your_number)
                return JsonResponse({'status': 'error', 'message': 'Invalid OTP'}, status=400)
        except json.JSONDecodeError as e:
            logger.error("JSON Decode Error: %s", str(e))
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'}, status=400)
        except Exception as e:
            logger.error("Unexpected Error: %s", str(e))
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

# Admin Views
@login_required
@staff_member_required
def admin_dashboard(request):
    bookings = Booking.objects.all()
    booking_details = []
    for booking in bookings:
        try:
            flight_details = json.loads(booking.flight_details)
        except json.JSONDecodeError:
            flight_details = {}

        booking_details.append({
            'ticket_number': booking.ticket_number,
            'user': booking.user.username,
            'outbound_flight': flight_details.get('outbound_flight', 'N/A'),
            'return_flight': flight_details.get('return_flight', 'N/A'),
            'date': flight_details.get('date', booking.created_at.strftime('%Y-%m-%d')),
            'total_price': booking.total_price,
            'email': booking.email,
        })

    context = {
        'bookings': booking_details,
        'total_bookings': bookings.count(),
        'pending_payments': sum(1 for b in booking_details if flight_details.get('payment_status') == 'Pending'),
    }
    return render(request, 'myapp/Admin/index.html', context)

@login_required
@staff_member_required
def admin_payment_history(request):
    bookings = Booking.objects.all()
    booking_details = []
    for booking in bookings:
        try:
            flight_details = json.loads(booking.flight_details)
        except json.JSONDecodeError:
            flight_details = {}

        booking_details.append({
            'id': booking.id,
            'ticket_number': booking.ticket_number,
            'payment_status': flight_details.get('payment_status', 'Pending'),
            'total_price': booking.total_price,
        })

    if request.method == 'POST':
        booking_id = request.POST.get('booking_id')
        action = request.POST.get('action')
        try:
            booking = Booking.objects.get(id=booking_id)
            flight_details = json.loads(booking.flight_details)
            if action == 'confirm':
                flight_details['payment_status'] = 'Completed'
                messages.success(request, f"Payment confirmed for booking {booking.ticket_number}.")
                Payment.objects.filter(flight_id=booking.outbound_id).update(status='completed')
                if booking.return_id:
                    Payment.objects.filter(flight_id=booking.return_id).update(status='completed')
            elif action == 'fail':
                flight_details['payment_status'] = 'Failed'
                messages.error(request, f"Payment marked as failed for booking {booking.ticket_number}.")
                Payment.objects.filter(flight_id=booking.outbound_id).update(status='failed')
                if booking.return_id:
                    Payment.objects.filter(flight_id=booking.return_id).update(status='failed')
            booking.flight_details = json.dumps(flight_details)
            booking.save()
        except Booking.DoesNotExist:
            messages.error(request, "Booking not found.")
        return redirect('admin_payment_history')

    payments = Payment.objects.all().order_by('-created_at')
    context = {
        'bookings': booking_details,
        'payments': payments,
    }
    return render(request, 'myapp/Admin/payment_history.html', context)

@login_required
@staff_member_required
def admin_users(request):
    travelers_data = []
    if request.method == 'POST':
        flight_id = request.POST.get('flight_id', '').strip()
        booking_id = request.POST.get('booking_id', '').strip()

        bookings = Booking.objects.all()

        # Filter by flight number (outbound_id or return_id)
        if flight_id:
            bookings = bookings.filter(
                models.Q(outbound_id__iexact=flight_id) |
                models.Q(return_id__iexact=flight_id)
            )

        # Filter by booking ID (outbound_booking_id or return_booking_id in flight_details)
        if booking_id:
            filtered_bookings = []
            for booking in bookings:
                try:
                    flight_details = json.loads(booking.flight_details)
                    outbound_booking_id = flight_details.get('outbound_booking_id', '')
                    return_booking_id = flight_details.get('return_booking_id', '')
                    if booking_id.lower() in [outbound_booking_id.lower(), return_booking_id.lower()]:
                        filtered_bookings.append(booking)
                except json.JSONDecodeError:
                    continue
            bookings = filtered_bookings

        # Dictionary to track booking counts per traveler
        traveler_counts = {}

        for booking in bookings:
            try:
                flight_details = json.loads(booking.flight_details)
                travelers = flight_details.get('travelers', [])
            except json.JSONDecodeError:
                travelers = []

            for traveler in travelers:
                traveler_key = (traveler.get('full_name', 'N/A'), traveler.get('email', 'N/A'))
                traveler_counts[traveler_key] = traveler_counts.get(traveler_key, 0) + 1

                if flight_id:
                    if booking.outbound_id == flight_id:
                        display_flight_id = booking.outbound_id
                    elif booking.return_id == flight_id:
                        display_flight_id = booking.return_id
                    else:
                        display_flight_id = booking.outbound_id or booking.return_id or 'N/A'
                else:
                    display_flight_id = booking.outbound_id or booking.return_id or 'N/A'

                # Determine the appropriate booking ID to display
                try:
                    flight_details = json.loads(booking.flight_details)
                    outbound_booking_id = flight_details.get('outbound_booking_id', 'N/A')
                    return_booking_id = flight_details.get('return_booking_id', '')
                    if booking_id:
                        if booking_id.lower() == outbound_booking_id.lower():
                            display_booking_id = outbound_booking_id
                        elif booking_id.lower() == return_booking_id.lower():
                            display_booking_id = return_booking_id
                        else:
                            display_booking_id = outbound_booking_id  # Default to outbound if no match
                    else:
                        display_booking_id = outbound_booking_id
                except json.JSONDecodeError:
                    display_booking_id = 'N/A'

                travelers_data.append({
                    'booking_id': display_booking_id,
                    'flight_id': display_flight_id,
                    'name': traveler.get('full_name', 'N/A'),
                    'email': traveler.get('email', 'N/A'),
                    'phone': traveler.get('mobile', 'N/A'),
                    'booking_count': traveler_counts[traveler_key],
                })

    context = {
        'travelers': travelers_data,
    }
    return render(request, 'myapp/Admin/users.html', context)

@login_required
@staff_member_required
def admin_notifications(request):
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'send_to_user':
            # Handle individual user notification
            user_email = request.POST.get('user_email')
            user_message = request.POST.get('user_message')

            if user_email and user_message:
                try:
                    # Send email to the individual user
                    subject = "Inido Airlines Notification"
                    message = (
                        f"Dear Passenger,\n\n"
                        f"{user_message}\n\n"
                        f"Best regards,\nInido Airlines Team"
                    )
                    from_email = settings.DEFAULT_FROM_EMAIL
                    send_mail(
                        subject=subject,
                        message=message,
                        from_email=from_email,
                        recipient_list=[user_email],
                        fail_silently=False,
                    )
                    logger.info(f"Sent notification email to {user_email}")

                    # Save the notification in the database
                    Notification.objects.create(
                        recipient=user_email,
                        message=user_message
                    )
                    messages.success(request, f"Notification sent successfully to {user_email}.")
                except Exception as e:
                    logger.error(f"Failed to send notification email to {user_email}: {str(e)}")
                    messages.error(request, f"Failed to send notification email: {str(e)}")
            else:
                messages.error(request, "Please provide both user email and message.")

        elif action == 'send_to_flight':
            # Handle flight-wide notification
            flight_number = request.POST.get('flight_id')  # Note: form uses 'flight_id' as name, but it's actually flight number
            flight_message = request.POST.get('flight_message')

            if flight_number and flight_message:
                try:
                    # Find all bookings for the flight
                    bookings = Booking.objects.filter(
                        models.Q(outbound_id__iexact=flight_number) |
                        models.Q(return_id__iexact=flight_number)
                    )

                    # Collect unique email addresses of affected passengers
                    email_list = set()
                    for booking in bookings:
                        try:
                            flight_details = json.loads(booking.flight_details)
                            travelers = flight_details.get('travelers', [])
                            for traveler in travelers:
                                traveler_email = traveler.get('email')
                                if traveler_email:
                                    email_list.add(traveler_email)
                        except json.JSONDecodeError:
                            logger.warning(f"Could not parse flight details for booking {booking.ticket_number}")

                    # Send email to all affected passengers
                    if email_list:
                        subject = f"Inido Airlines Notification for Flight Number {flight_number}"
                        message = (
                            f"Dear Passenger,\n\n"
                            f"{flight_message}\n\n"
                            f"Best regards,\nInido Airlines Team"
                        )
                        from_email = settings.DEFAULT_FROM_EMAIL
                        send_mail(
                            subject=subject,
                            message=message,
                            from_email=from_email,
                            recipient_list=list(email_list),
                            fail_silently=False,
                        )
                        logger.info(f"Sent notification emails to {len(email_list)} passengers for flight {flight_number}")

                        # Save the notification in the database
                        Notification.objects.create(
                            recipient=f"All passengers of flight {flight_number}",
                            message=flight_message
                        )
                        messages.success(request, f"Notification sent successfully to {len(email_list)} passengers of flight {flight_number}.")
                    else:
                        messages.info(request, f"No passengers found for flight {flight_number} to notify.")
                except Exception as e:
                    logger.error(f"Failed to send flight notification emails for flight {flight_number}: {str(e)}")
                    messages.error(request, f"Failed to send flight notification emails: {str(e)}")
            else:
                messages.error(request, "Please provide both flight number and message.")

        return redirect('admin_notifications')

    # Display recent notifications
    recent_notifications = Notification.objects.all().order_by('-created_at')
    context = {
        'recent_notifications': recent_notifications,
    }
    return render(request, 'myapp/Admin/notifications.html', context)

@login_required
@staff_member_required
def admin_flight_delays(request):
    if request.method == 'POST':
        flight_number = request.POST.get('flight_number')
        reason = request.POST.get('reason')
        delay_duration = request.POST.get('delay_duration')
        if flight_number and reason and delay_duration:
            try:
                delay_duration = int(delay_duration)
                # Create the flight delay record
                flight_delay = FlightDelay.objects.create(
                    flight_number=flight_number,
                    reason=reason,
                    delay_duration=delay_duration
                )
                messages.success(request, f"Delay added for flight number {flight_number}.")

                # Find all bookings for the delayed flight
                bookings = Booking.objects.filter(
                    models.Q(outbound_id__iexact=flight_number) |
                    models.Q(return_id__iexact=flight_number)
                )

                # Collect email addresses of affected users
                email_list = []
                for booking in bookings:
                    try:
                        # Extract traveler emails from flight_details
                        flight_details = json.loads(booking.flight_details)
                        travelers = flight_details.get('travelers', [])
                        for traveler in travelers:
                            traveler_email = traveler.get('email')
                            if traveler_email and traveler_email not in email_list:
                                email_list.append(traveler_email)
                    except json.JSONDecodeError:
                        logger.warning(f"Could not parse flight details for booking {booking.ticket_number}")

                # Send email notifications to all affected users
                if email_list:
                    subject = f"Flight Delay Notification for Flight Number {flight_number}"
                    message = (
                        f"Dear Passenger,\n\n"
                        f"We regret to inform you that your flight, Flight Number {flight_number}, "
                        f"has been delayed by {delay_duration} minutes. "
                        f"Reason for the delay: {reason}.\n\n"
                        f"We apologize for the inconvenience and appreciate your understanding.\n\n"
                        f"Best regards,\nInido Airlines Team"
                    )
                    from_email = settings.DEFAULT_FROM_EMAIL
                    try:
                        send_mail(
                            subject=subject,
                            message=message,
                            from_email=from_email,
                            recipient_list=email_list,
                            fail_silently=False,
                        )
                        logger.info(f"Sent delay notification emails to {len(email_list)} users for flight {flight_number}")
                        messages.success(request, f"Sent delay notification emails to {len(email_list)} affected passengers.")
                    except Exception as e:
                        logger.error(f"Failed to send delay notification emails for flight {flight_number}: {str(e)}")
                        messages.error(request, f"Failed to send delay notification emails: {str(e)}")
                else:
                    messages.info(request, "No passengers found for this flight to notify.")

            except ValueError:
                messages.error(request, "Delay duration must be a number.")
        else:
            messages.error(request, "Please fill in all fields.")
        return redirect('admin_flight_delays')
    delays = FlightDelay.objects.all().order_by('-created_at')
    context = {
        'delays': delays,
    }
    return render(request, 'myapp/Admin/flight_delays.html', context)

@login_required
@staff_member_required
def admin_user_queries(request):
    if request.method == 'POST':
        query_id = request.POST.get('query_id')
        action = request.POST.get('action')
        try:
            query = UserQuery.objects.get(query_id=query_id)
            if action == 'resolve':
                query.status = 'resolved'
                query.save()
                messages.success(request, f"Query {query_id} marked as resolved.")
        except UserQuery.DoesNotExist:
            messages.error(request, "Query not found.")
        return redirect('admin_user_queries')
    
    queries = UserQuery.objects.all().order_by('-submission_date')
    query_details = []
    for query in queries:
        # Parse query_text to extract subject and message
        query_text = query.query_text
        subject = "N/A"
        message = "N/A"
        if query_text:
            parts = query_text.split('\n', 1)  # Split on the first newline
            if len(parts) > 0 and parts[0].startswith("Subject: "):
                subject = parts[0].replace("Subject: ", "", 1).strip()
            if len(parts) > 1 and parts[1].startswith("Message: "):
                message = parts[1].replace("Message: ", "", 1).strip()
        
        # Log the email being fetched to debug
        logger.debug("Fetching email for user %s: %s", query.user.username, query.user.email)
        
        # Check if the user's email is empty or None, and provide a fallback
        user_email = query.user.email if query.user.email else "Email not set"
        
        query_details.append({
            'query_id': query.query_id,
            'username': query.user.username,
            'email': user_email,
            'subject': subject,
            'message': message,
        })
    
    context = {
        'queries': query_details,
    }
    return render(request, 'myapp/Admin/user_queries.html', context)

@login_required
@staff_member_required
def admin_logout(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('admin_signin')

@login_required
def help_desk(request):
    if request.method == 'POST':
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        if subject and message:
            # Combine subject and message into query_text
            query_text = f"Subject: {subject}\nMessage: {message}"
            max_attempts = 5
            attempt = 0
            while attempt < max_attempts:
                try:
                    query_id = str(uuid.uuid4())
                    UserQuery.objects.create(
                        user=request.user,
                        query_id=query_id,
                        query_text=query_text,
                        status='pending'
                    )
                    logger.info("User query submitted successfully by %s, query_id: %s", request.user.username, query_id)
                    messages.success(request, "Your query has been submitted successfully!")
                    break
                except IntegrityError as e:
                    attempt += 1
                    logger.warning("Query ID collision on attempt %d for user %s: %s", attempt, request.user.username, str(e))
                    if attempt == max_attempts:
                        logger.error("Failed to generate unique query_id after %d attempts for user %s", max_attempts, request.user.username)
                        messages.error(request, "Failed to submit query due to a system error. Please try again later.")
                        break
                except Exception as e:
                    logger.error("Failed to submit query for user %s: %s", request.user.username, str(e))
                    messages.error(request, f"Failed to submit query: {str(e)}")
                    break
        else:
            logger.warning("Help desk form submitted with missing fields by user %s: subject=%s, message=%s", 
                          request.user.username, subject, message)
            messages.error(request, "Please fill in all fields.")
        return redirect('help_desk')
    
    user_queries = UserQuery.objects.filter(user=request.user).order_by('-submission_date')
    return render(request, 'myapp/User/help_desk.html', {'user_queries': user_queries})

@login_required
@staff_member_required
def admin_seat_inventory(request):
    # Sample data for demonstration
    flights = [
        {
            'flight_number': '6E-1442',
            'available_seats': {'economy': 120, 'business': 20, 'first_class': 8},
            'total_seats': 148,
            'load_factor': 75,
            'departure_date': '2025-05-10',
            'status': 'On Time'
        },
        {
            'flight_number': '6E-1573',
            'available_seats': {'economy': 100, 'business': 15, 'first_class': 5},
            'total_seats': 120,
            'load_factor': 82,
            'departure_date': '2025-05-12',
            'status': 'Delayed'
        },
    ]

    # Calculate total seats by class
    total_seats = {
        'economy': sum(flight['available_seats']['economy'] for flight in flights),
        'business': sum(flight['available_seats']['business'] for flight in flights),
        'first_class': sum(flight['available_seats']['first_class'] for flight in flights),
    }

    # Calculate number of flights by class (assuming a flight has seats in a class if the count is > 0)
    flight_counts = {
        'economy': sum(1 for flight in flights if flight['available_seats']['economy'] > 0),
        'business': sum(1 for flight in flights if flight['available_seats']['business'] > 0),
        'first_class': sum(1 for flight in flights if flight['available_seats']['first_class'] > 0),
    }

    context = {
        'flights': flights,
        'total_seats': total_seats,
        'flight_counts': flight_counts,
    }
    return render(request, 'myapp/Admin/seat_inventory.html', context)


