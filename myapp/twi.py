from twilio.rest import Client
import random

otp = random.randint(1000, 9999)


# Twilio credentials from https://www.twilio.com/console
account_sid = 'id'
auth_token = 'token'

# Initialize client
client = Client(account_sid, auth_token)

# Send message
message = client.messages.create(
    body=f"Hey! This Is A Test Message From Inido Airlines...Your OTP Is {otp}",     # Message text
    from_='num',                      # Twilio phone number
    to='+91'                          # Your verified phone number
)

print("Message SID:", message.sid)
print("Message sent successfully!")
