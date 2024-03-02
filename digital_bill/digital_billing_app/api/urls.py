from django.urls import path, include
from digital_billing_app.api.views import *

urlpatterns = [
    path('api_registration/', api_registration, name= 'api_registration'),
    path('api_confirm_otp/', api_confirmOTPCode, name= 'api_confirm_otp'),
    path('api_re_generate_otp/', api_re_generate_otp, name= 'api_re_generate_otp'),
    path('api_secure_pin/', api_securePin, name= 'api_secure_pin'),
    path('api_login/', api_login, name= 'api_login'),
    path('api_login_with_pin/', api_login_with_pin, name= 'api_login_with_pin'),
    path('api_dataSubscription/', api_dataSubscription, name= 'api_dataSubscription'),
    path('api_set_updateAcct/', api_set_updateAcct, name= 'api_set_updateAcct'),
    path('api_getProfileInfo/', api_getProfileInfo, name= 'api_getProfileInfo'),
    path('api_logoutUser/', api_logoutUser, name= 'api_logoutUser'),
    path('api_changePassword/', api_changePassword, name= 'api_changePassword'),
    path('api_deactivateAccount/', api_deactivateAccount, name= 'api_deactivateAccount'),
    path('api_authenticateWithBiometrics/', api_authenticateWithBiometrics, name= 'api_authenticateWithBiometrics'),
    path('api_processTransaction/', api_processTransaction, name= 'api_processTransaction'),
    path('api_acctTransactionLog/', api_acctTransactionLog, name= 'api_acctTransactionLog'),
    path('api_acctStatement/', api_acctStatement, name= 'api_acctStatement'),
    path('api_acctProfilePix/', api_acctProfilePix, name= 'api_acctProfilePix'),
    path('api_creditCusWallet/', api_creditCusWallet, name= 'api_creditCusWallet'),
    path('api_referrals/', api_referrals, name= 'api_referrals'),

    
    path('api/password_reset/', include('django_rest_passwordreset.urls', namespace='password_reset')),
]