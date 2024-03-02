from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin

# from digital_billing_app.api.serializers import CustomUserChangeForm, CustomUserCreationForm
from .models import AccountHistory, CustomUser, DataSubscription, CompanyInfo

# Register your models here.

class CustomUserAdmin(admin.ModelAdmin):
    # add_form = CustomUserCreationForm
    # form = CustomUserChangeForm
    # model = CustomUser
    list_display = ["email", "name", "mobile_no",]

class DataSubscriptionAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "amount_mb", "price", "period", "discount", "active"]

class AccountHistoryAdmin(admin.ModelAdmin):
    list_display = ["transaction_date", "description", "credit", "debit", "closing_bal", "status"]
    readonly_fields = ['closing_bal', 'status', 'debit', 'transaction_log']

class CompanyInfoAdmin(admin.ModelAdmin):
    list_display = ["business_name", "street_address1", "state", "country", "phone", "email", "updated_date"]


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(DataSubscription, DataSubscriptionAdmin)
admin.site.register(AccountHistory, AccountHistoryAdmin)
admin.site.register(CompanyInfo, CompanyInfoAdmin)