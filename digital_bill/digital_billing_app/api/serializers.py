from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework.exceptions import ValidationError
from django import forms

from digital_billing_app.models import CustomUser, AccountHistory, Referral




class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    name = forms.CharField(required=True)
    password1 = forms.CharField(widget=forms.PasswordInput(), required=True)
    password2 = forms.CharField(widget=forms.PasswordInput(), required=True)
    mobile_no = forms.CharField(required=True)
    unique_referral_code = forms.CharField(required=True)
    ur_referred_code = forms.CharField(required=False)
    class Meta:
        model = CustomUser
        fields = ('name', 'email', 'mobile_no', "password1", "password2", "unique_referral_code", "ur_referred_code")

    # def save(self, commit=True):
    #     user = super().save(commit=False)

    #     email = self.cleaned_data.get('email')
    #     if User.objects.filter(email=email).exists():
    #         raise ValidationError('Email already exist')
    #     user.email = self.cleaned_data['email']

    #     if commit:
    #         user.save()
    #     return user

class UpddateCustomCreationFormProfile(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('image', 'discoverUs')


class ReferralForm(serializers.ModelSerializer):
    # referred_cus = forms.IntegerField(required=True)
    # referred_cus_initial_deposit = forms.FloatField(required=False)
    # percentage_rate = forms.FloatField(required=True)
    referral_process = forms.CharField(required=True)
    class Meta:
        model = Referral
        fields = ('referral_customer', 'percentage_rate', "referral_process")


class AccountForm(serializers.ModelSerializer):
    credit = forms.FloatField(required=True)
    description = forms.CharField(required=False)

    class Meta:
        model = AccountHistory
        fields = ('description', 'credit', 'status', 'payVerify', 'payMethod', 'payCard')


# class CustomUserChangeForm(serializers.ModelSerializer):
#     # email = forms.EmailField(required=True)
#     # name = forms.CharField(required=True)
#     # password = forms.CharField(widget=forms.PasswordInput(), required=True)
#     # _password = forms.CharField(widget=forms.PasswordInput(), required=True)
#     # mobile_no = forms.CharField(required=True)
#     class Meta:
#         model = CustomUser
#         fields = ("name", "email", "mobile_no", "password", "_password")


# class CreateUserForm(UserCreationForm):
#     first_name = forms.CharField(required=True)
#     last_name = forms.CharField(required=True)
#     email = forms.EmailField(required=True)
#     username = forms.CharField(required=True)
#     password1 = forms.CharField(widget=forms.PasswordInput(), required=True)
#     password2 = forms.CharField(widget=forms.PasswordInput(), required=True)
#     prefix = forms.CharField(required=True)
#     businessName = forms.CharField(required=True)
#     mobile = forms.CharField(required=True)
#     streetAddress1 = forms.CharField(required=True)
#     city = forms.CharField(required=True)
#     state = forms.CharField(required=True)
#     country = forms.CharField(required=True)
#     discoverUs = forms.CharField(required=True)
#     class Meta:
#         model = User
#         fields = ['first_name', 'last_name', 'username', 'email', 'password1', 
#             'password2', 'prefix', 'businessName', 'mobile', 'streetAddress1',
#             'city', 'state', 'country', 'discoverUs'
#         ]
