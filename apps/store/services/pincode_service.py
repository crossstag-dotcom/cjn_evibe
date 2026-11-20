import re

def clean_office_name(name):
    """
    Remove India Post suffixes from office names.
    """
    return re.sub(r"\s+(H\.O|S\.O|B\.O)$", "", name).strip()

from dataclasses import dataclass

@dataclass
class PincodeResult:
    success: bool
    message: str = ""

    pincode: str = ""
    city: str = ""
    district: str = ""
    state: str = ""

from apps.store.models import Pincode

def get_location_from_pincode(pincode):

    pincode = pincode.strip()

    if len(pincode) != 6 or not pincode.isdigit():
        return PincodeResult(
            success=False,
            message="Invalid PIN Code"
        )

    offices = Pincode.objects.filter(
        pincode=pincode
    )

    if not offices.exists():
        return PincodeResult(
            success=False,
            message="PIN Code not found"
        )

    office = (
        offices.filter(office_name__iendswith="H.O").first()
        or offices.filter(office_name__icontains="GPO").first()
        or offices.filter(office_name__icontains="City").first()
        or offices.first()
    )

    return PincodeResult(
        success=True,
        pincode=office.pincode,
        city=clean_office_name(office.office_name),
        district=office.district,
        state=office.state,
    )