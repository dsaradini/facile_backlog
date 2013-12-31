from django.contrib import admin

from .models import (Ticket, Message)


class TicketAdmin(admin.ModelAdmin):
    list_display = ("text", "status", "modification_date", "email", "category")
    search_fields = ("text", "email")
    list_filter = ("status", "category")


class MessageAdmin(admin.ModelAdmin):
    list_display = ("text", "creation_date", "ticket")
    search_fields = ("text", "ticket__text")
    readonly_fields = ("ticket", "creation_date")

admin.site.register(Ticket, TicketAdmin)
admin.site.register(Message, MessageAdmin)
