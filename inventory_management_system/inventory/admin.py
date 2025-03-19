from django.contrib import admin
from .models import CDSR, DDSR , ConsumeCDSR,ConsumeDDSR , WriteOff

# Register your models here.
admin.site.register(CDSR)
admin.site.register(DDSR)
admin.site.register(ConsumeCDSR)
admin.site.register(ConsumeDDSR)
admin.site.register(WriteOff)
