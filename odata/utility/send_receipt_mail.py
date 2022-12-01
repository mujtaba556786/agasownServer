from Project.settings import EMAIL_HOST_USER
from django.core.mail import send_mail
from django.http.response import JsonResponse


def send_mail_card(customer_email, retrieve_url, name, payment_method_type, card_brand, last_digits, card_type):
    email_body = f"Hi {name},\n Thank you for making the payment. We have received your payment \n Transaction Details:\n Payment Method: {payment_method_type}\n Card Brand: {card_brand} \n Card Ending digits:xxxx-xxxx-xxxx-{last_digits}\n Card Type: {card_type} \n " \
                 f"Here is the  link for your reciept {retrieve_url} \n Your order will be delivered within 3 working days.\n " \
                 f"You will receive an email shortly after it's dispatched.\n Best wishes,\n AgasOwn Marketing Team \n"
    try:
        send_mail(
            subject='Agas Own Successful Payment',
            message=email_body,
            from_email=EMAIL_HOST_USER,
            recipient_list=[customer_email],
            fail_silently=False)
    except Exception as e:
        return JsonResponse({"Message": e},
                            status=500)


def send_mail_sofort(customer_email, customer_name, payment_type, bank_name, bank_code, last_digits):
    email_body = f"Hi {customer_name},\n Thank you for making the payment. We have received your payment \n Transaction Details:\n Payment Method: {payment_type}\n Bank Name: {bank_name} \n Bank Code: {bank_code}\n Account No. ending: {last_digits} \n " \
                 f"\n Your order will be delivered within 3 working days. You will receive an email shortly after it's dispatched.\n " \
                 f"\n Best wishes,\n AgasOwn Marketing Team \n"
    try:
        send_mail(
            subject='Agas Own Successful Payment',
            message=email_body,
            from_email=EMAIL_HOST_USER,
            recipient_list=[customer_email],
            fail_silently=False)
    except Exception as e:
        return JsonResponse({"Message": e},
                            status=500)


def send_mail_paypal(first_name,last_name, email, product_name, quantity, price, total_amount):
    email_body = f"Hi {first_name} {last_name} ,\n Here is your Order Summary: \n" \
                 f"Product Name: " + product_name + "\n Product Quantity: " + quantity + "\n Product Price: " + price + "\n " \
                 f"Total Amount paid: " + total_amount + "\n Mode of payment: PayPal \n " \
                 f"Your order will be delivered within 3 working days. You will receive an email shortly after it's dispatched.\n " \
                 f"Best wishes,\n AgasOwn Marketing Team \n "

    try:
        send_mail(
            subject='Payment Successful for PayPal',
            message=email_body,
            from_email=EMAIL_HOST_USER,
            recipient_list=[email],
            fail_silently=False)
    except Exception as e:
        return JsonResponse({"Message": e},
                            status=500)
