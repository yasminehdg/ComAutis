from django.contrib import admin
from .models import Level, Subscription

@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'description')
    list_filter = ('price',)
    search_fields = ('name',)

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'parent', 'level', 'start_date', 'end_date', 'active', 'simulated_payment_id')
    list_filter = ('active', 'level', 'start_date')
    search_fields = ('parent__username', 'level__name', 'simulated_payment_id')
    date_hierarchy = 'start_date'