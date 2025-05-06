from django.shortcuts import render, redirect


def login_redirects(request):
    if request.user.is_authenticated:
        # TODO: TEMPLATE LOGIN REDIRECTS GO HERE
        return redirect("dashboard")
    return redirect("login")


def index(request):
    return render(request, template_name="index.html")


# ----------------------------------------------------------------
# ----------------------------TEST URLS---------------------------
# ----------------------------------------------------------------
def testing_sbadmin2(request):
    return render(request, template_name="testing/testing_sbadmin2.html")
