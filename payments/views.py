from django.contrib import messages
from django.shortcuts import redirect, render
import stripe
from stripe.api_resources import source
from stripe.api_resources.abstract import createable_api_resource
stripe.api_key = "sk_test_51JWasjC3vmDAEiznCKhV7YRb40NKUslBuCnDQRi536NwbX2i2FcdsxS5qFeIV2J0RjFbsQN4E2YcVCUTnvIFstvd00L7GAQjs8"


def checkout(request):
    payment_methods = [
        'Paypal',
        'Stripe'
    ]
    return render(request, 'payments/checkout.html', {'payment_methods': payment_methods,})


def charge(request):
    if request.method == 'POST':
        print('DATA:', request.POST)

        customer = stripe.Customer.create(
            email=request.POST['email'],
            name=request.POST['name'],
            source=request.POST['token'],
        )
        charge = stripe.Charge.create(
            customer=customer,
            amount=int(request.POST['amount']) *100,
            currency='usd',
            description='Product buy'

        )
    return redirect('payments')
