from django.shortcuts import render
from django.http import HttpResponse

def home(request):
    return HttpResponse("TEAM6: 動作確認OK")
