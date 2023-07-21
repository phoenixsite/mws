from django.shortcuts import render

def home(request):
    reg_link = "register"
    return render(
        request,
        "mws_main/home.html",
        {"reg_link": reg_link}
    )
