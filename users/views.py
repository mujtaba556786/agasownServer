from django import forms
from django.shortcuts import render, redirect
from django.contrib import messages
from .form import UserRegisterForm
from django.contrib.auth.models import User


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        email = request.POST['email']

        if User.objects.filter(email=email).exists():
            messages.error(request, f'{email} already exists')
            return redirect('/register')
           
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            return redirect('login')
           

    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form})

def welcome(request):
    return render(request, 'users/welcome.html', {'user': request.user})