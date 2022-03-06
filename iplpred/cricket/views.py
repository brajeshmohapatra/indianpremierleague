from django.shortcuts import redirect, render, get_object_or_404
# Create your views here.


def home(request ):
    return render (request, 'cricket/home.html')


