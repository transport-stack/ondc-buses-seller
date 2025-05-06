from main.models import TicketType, Ticket, PassType, Pass
from main.models.fare_setup import FareBreakup
from main.models.pass_fare_setup import PassFareBreakup
from main.models.tickets import Agency


class PassAndPassFareSetup():
    @staticmethod
    def create_pass(pnr, pass_status, transit_pnr, pass_name, amount, fare, valid_till,
                    subscriber_id, is_ac, agency, claim_status, user_details):
        try:
            pass_type = PassType.objects.get(name=pass_name)
            agency_obj = Agency.objects.get(name=agency) if agency is not None else None
        except TicketType.DoesNotExist:
            agency_obj = None
            pass_type = None

        bus_pass = Pass.objects.create(
            pnr=pnr,
            pass_status=pass_status,
            transit_pnr=transit_pnr,
            pass_type=pass_type,
            user_name=user_details['name'],
            phone_number=user_details['phone_number'],
            email=user_details['email'],
            govt_id=user_details['govt_id'],
            govt_id_number=user_details['govt_id_number'],
            photo=user_details['photo'],
            amount=amount,
            fare=fare,
            valid_till=valid_till,
            agency=agency_obj,
            subscriber_id=subscriber_id,
            is_ac=is_ac,
            claim_status=claim_status
        )
        return bus_pass

    @staticmethod
    def create_pass_fare_breakup(basic, amount, toll, convenience_charge, convenience_charge_tax, franchisee_service_charge, discount,
                                 add_on, add_on_tax, cancellation_chg, coupon, coupon_discount):
        fare_breakup = PassFareBreakup.objects.create(
            basic=basic,
            amount=amount,
            toll=toll,
            convenience_charge=convenience_charge,
            convenience_charge_tax=convenience_charge_tax,
            franchisee_service_charge=franchisee_service_charge,
            discount=discount,
            add_on=add_on,
            add_on_tax=add_on_tax,
            cancellation_chg=cancellation_chg,
            coupon=coupon,
            coupon_discount=coupon_discount
        )
        return fare_breakup
