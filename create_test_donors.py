from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point

from apps.accounts.models import Profile


User = get_user_model()

test_users = [
    {
        "full_name": "Ram Thapa",
        "email": "ram.test@pulze.com",
        "blood_type": "A+",
        "is_donor": True,
        "latitude": 27.670000,
        "longitude": 84.455000,
    },
    {
        "full_name": "Suman KC",
        "email": "suman.test@pulze.com",
        "blood_type": "A-",
        "is_donor": True,
        "latitude": 27.700000,
        "longitude": 84.480000,
    },
    {
        "full_name": "Hari Gurung",
        "email": "hari.test@pulze.com",
        "blood_type": "O+",
        "is_donor": True,
        "latitude": 27.730000,
        "longitude": 84.520000,
    },
    {
        "full_name": "Sita Sharma",
        "email": "sita.test@pulze.com",
        "blood_type": "B+",
        "is_donor": True,
        "latitude": 27.800000,
        "longitude": 84.600000,
    },
    {
        "full_name": "Ramesh Adhikari",
        "email": "ramesh.test@pulze.com",
        "blood_type": "O-",
        "is_donor": False,
        "latitude": 27.700000,
        "longitude": 84.480000,
    },
]

password = "Test@12345"


for data in test_users:
    user, created = User.objects.get_or_create(
        email=data["email"],
        defaults={
            "full_name": data["full_name"],
            "is_email_verified": True,
            "is_active": True,
        },
    )

    if created:
        user.set_password(password)
        user.save()

    profile, _ = Profile.objects.get_or_create(
        user=user,
        defaults={
            "is_donor": data["is_donor"],
            "blood_type": data["blood_type"],
            "gender": "other",
            "date_of_birth": "2000-01-01",
            "location": Point(
                data["longitude"],
                data["latitude"],
                srid=4326,
            ),
        },
    )

    profile.is_donor = data["is_donor"]
    profile.blood_type = data["blood_type"]
    profile.location = Point(
        data["longitude"],
        data["latitude"],
        srid=4326,
    )
    profile.save()

    print(
        f"{'Created' if created else 'Updated'}: "
        f"{user.email} | "
        f"{profile.blood_type} | "
        f"Donor: {profile.is_donor}"
    )