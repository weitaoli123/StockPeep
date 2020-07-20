"""mysite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""

from django.conf.urls import url
from django.urls import path
from django.contrib import admin
from . import views
# from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$',views.signInPage,name="signInPage"),
    url(r'^signin/',views.signIn),
    url(r'^logout/',views.logout,name="logout"),
    url(r'^register/',views.register),
    url(r'^watchlist/',views.watchlist, name="watchlist"),
    url(r'^findTicker/',views.get_company_name,name="get_company_name"),
    url(r'^addWatchlist/(?P<ticker>.+)/(?P<name>.+)/',views.addWatchlist,name="addWatchlist"),
    url(r'^removeWatchlist/(?P<id>.+)/',views.removeWatchlist,name="removeWatchlist"),
    path('home/',views.home, name="home"),
    path('registerPage/',views.registerPage,name="registerPage"),
    # path('home_main/',views.home,name="home_main"),
    # path('signin/',views.signIn,name='signin'),
]

