from django.db import transaction

from .models import Donor


@transaction.atomic
def activate_user_donor(profile):
    donor, created = Donor.objects.get_or_create(
        profile=profile,
        defaults={
            "donor_type": Donor.USER,
            "blood_type": profile.blood_type,
            "is_active": True,
            "source": Donor.APP,
        },
    )

    if not created:
        donor.donor_type = Donor.USER
        donor.blood_type = profile.blood_type
        donor.is_active = True
        donor.source = Donor.APP
        donor.save(
            update_fields=[
                "donor_type",
                "blood_type",
                "is_active",
                "source",
                "updated_at",
            ],
        )

    return donor


@transaction.atomic
def deactivate_user_donor(profile):
    donor = Donor.objects.filter(
        profile=profile,
    ).first()

    if donor is not None:
        donor.is_active = False
        donor.save(
            update_fields=[
                "is_active",
                "updated_at",
            ],
        )

    return donor