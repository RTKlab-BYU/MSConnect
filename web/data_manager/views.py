from django.contrib.auth import authenticate, login
from django.shortcuts import redirect, render


from .forms import SignUpForm


def signup(request):
    """_User sign up page_
    """
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})


def contact(request):

    return render(request, 'registration/contact.html')
