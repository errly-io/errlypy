import asyncio

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def view_zero_division(request):
    1 / 0


async def async_view_zero_division(request):
    1 / 0


async def async_view_zero_division_sleep_3_sec(request):
    await asyncio.sleep(3)
    1 / 0


async def async_view_ok(request):
    return HttpResponse("ok")


async def async_view_ok_sleep_3_sec(request):
    await asyncio.sleep(3)
    return HttpResponse("ok")
