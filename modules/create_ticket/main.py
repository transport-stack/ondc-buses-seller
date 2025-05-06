from main.models import TicketType, Ticket
from main.models.fare_setup import FareBreakup
from main.models.tickets import Agency


class TicketAndFareSetup():
    def create_ticket(self, pnr, ticket_status, transit_pnr, ticket_type_id,
                      passenger_count, amount, payment_type, payment_status,fare, valid_till,
                      vehicle_number, start_stop_name, start_stop_code, end_stop_name, end_stop_code, route,
                      subscriber_id, description, is_ac, agency, claim_status):
        try:
            ticket_type = TicketType.objects.get(id=ticket_type_id)
            agency_obj = Agency.objects.get(name=agency) if agency is not None else None
        except TicketType.DoesNotExist:
            agency_obj = None
            ticket_type = None

        ticket = Ticket.objects.create(
            pnr=pnr,
            ticket_status=ticket_status,
            transit_pnr=transit_pnr,
            ticket_type=ticket_type,
            passenger_count=passenger_count,
            amount=amount,
            payment_type=payment_type,
            payment_status=payment_status,
            fare=fare,
            valid_till=valid_till,
            vehicle_number=vehicle_number,
            agency=agency_obj,
            start_stop_name=start_stop_name,
            start_stop_code=start_stop_code,
            end_stop_name=end_stop_name,
            end_stop_code=end_stop_code,
            route=route,
            subscriber_id=subscriber_id,
            description=description,
            is_ac=is_ac,
            claim_status=claim_status
        )
        return ticket

    def create_fare_breakup(self, basic, amount, toll, convenience_charge,
                            convenience_charge_tax, franchisee_service_charge, discount,
                            add_on, add_on_tax, cancellation_chg, coupon,
                            coupon_discount):
        fare_breakup = FareBreakup.objects.create(
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
