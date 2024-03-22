
import os
from shutil import ExecError
from struct import pack_into
from unittest import IsolatedAsyncioTestCase
from urllib import response
# from tkinter.tix import Tree
from django.http import HttpResponse, JsonResponse
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth.forms import PasswordChangeForm
from .serializers import CustomUserCreationForm, ReferralForm, AccountForm, UpddateCustomCreationFormProfile
from digital_billing_app.models import *
from digital_billing_app.api.utils import get_otp, verifyUser, toJsonDataSub, verifyUser2, serviceTransaction, convertReferralToJsonRecord
from datetime import datetime, timedelta
import pyotp
import uuid
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password, check_password
from digital_billing_app.decorators import unauthenticated_user, allowed_user
from django.http import HttpRequest
from decouple import config


@api_view(['POST'])
def api_registration(request):
    data = {}
    data['isSuccess'] = False
    data['errorMsg'] = ''
    data['otp_code'] = ''
    isRefRequired = False
    data['refCreated'] = ''
    try:
        if request.method == 'POST':
          
            form = CustomUserCreationForm(data=request.data)
            if form.is_valid():
                if CustomUser.objects.filter(email= request.data['email']).exists():
                    data['errorMsg'] = 'A user with this email address already exist!'
                    return JsonResponse(data)
                elif CustomUser.objects.filter(mobile_no= request.data['mobile_no']).exists():
                    data['errorMsg'] = 'Account with this mobile number already exist!'
                    return JsonResponse(data)
                elif request.data['ur_referred_code'] != '' and request.data['ur_referred_code'] is not None:
                    if not CustomUser.objects.filter(unique_referral_code= request.data['ur_referred_code']).exists():
                        data['errorMsg'] = {'referral_code': 'Wrong referral Code'}
                        return JsonResponse(data)
                    else:
                        
                        isRefRequired = True
                        
                            
                acct = form.save()
                data = {
                    'id': acct.id,
                    'name': acct.name,
                    'token': acct.auth_token.key,
                    'email': acct.email,
                    'mobile': acct.mobile_no,
                }
                if isRefRequired:
                    bonusRate = CompanyInfo.objects.get(id= 1)
                    referral_cus = CustomUser.objects.get(unique_referral_code= request.data['ur_referred_code'])
                    # THERE IS A REFERRAL CODE. SAVE REFERRAL TO THE TABLE
                    refCreated = Referral.objects.create(
                        referral_customer = referral_cus,
                        referred_cus = acct.id,
                        percentage_rate = bonusRate.bonus_percent,
                        referral_process = 'Processing'
                    )   
                    data['refCreated'] = refCreated.id
                otp_code = get_otp(request)
                data['otp_secret_key'] = otp_code['otp_secret_key']
                data['otp_valid_date'] = otp_code['otp_valid_date']
                data['otp_code'] = otp_code['otp']
                data['isSuccess'] = True
                print(data['otp_secret_key'])
            else:
                data['errorMsg'] = form.errors
            
    except Exception as e:
        data['errorMsg'] = e.args

    return JsonResponse(data)



# RE-GENERATE OTP CODE 
# @unauthenticated_user
@api_view(['POST'])
def api_re_generate_otp(request):
    data = {}
    data['isSuccess'] = False
    data['errorMsg'] = ''
    data['otp_code'] = ''
    try:
        otp_code = get_otp(request)
        data['otp_secret_key'] = otp_code['otp_secret_key']
        data['otp_valid_date'] = otp_code['otp_valid_date']
        data['otp_code'] = otp_code['otp']
        data['isSuccess'] = True
    except Exception as e:
        data['errorMsg'] = e.args

    return JsonResponse(data)


# OTP CONFIRM CODE 
# @unauthenticated_user
# @allowed_user
@api_view(['POST'])
def api_confirmOTPCode(request):
    data = {}
    data['isSuccess'] = False
    data['errorMsg'] = ''
    print('PASS')
    try:
        if request.user.is_authenticated:
            # user = CustomUser.objects.get(id=request.user.id)
            # user.security_pin = None
            # user.save()
            
            otp = str(request.data['otp'])
            otp_secret_key = request.data['otp_secret_key']
            otp_valid_date = request.data['otp_valid_date']
            print(otp)
            print(otp_secret_key)
            print(otp_valid_date)
            if otp_secret_key and otp_valid_date is not None:
                    valid_until = datetime.fromisoformat(otp_valid_date)
                    
                    if valid_until > datetime.now():
                        
                        totp = pyotp.TOTP(otp_secret_key, interval=60, digits=5)
                        
                        if totp.verify(otp):
                            
                            # UPDATE THE DATABASE TABLE THAT ACCT HAVE BEEN VIERIFIED THROUGH OTP
                            # DELETE THE OTP RECORD WE SAVED IN THE REQUEST SESSION
                            # REDIRECT TO THE PROFILE PAGE...
                            userProfile = CustomUser.objects.get(id= request.user.id)
                            userProfile.otpConfirm = True
                            userProfile.save()

                            data['isSuccess'] = True
                        else:
                            data['errorMsg'] = 'Wrong code!'
                    else:
                        data['errorMsg'] = 'Your verification code have expired. Kindly generate another to expire in 1 minutes'
            else:
                data['errorMsg'] = 'Kindly re-generate OTP code'
        else:
            
            data['errorMsg'] = 'User is not authenticated!'
    except Exception as e:
        data['errorMsg'] = e.args

    return JsonResponse(data)



# SAVE SECURE PIN OR CHANGE SECURE PIN
# @unauthenticated_user
@api_view(['POST'])
def api_securePin(request):
    data = {}
    data['isSuccess'] = False
    data['errorMsg'] = ''
    user = ''
    try:
        user = request.user
        if user.security_pin is None:
            user.security_pin = make_password(request.data['pin'])
            user.save()
            data['isSuccess'] = True
        elif (request.data['email'] is None or request.data['email'] == '') and (request.data['userName'] is None or request.data['userName'] == '') and (request.data['oldPin'] is None or request.data['oldPin'] == '') and (request.data['newPin'] is None or request.data['newPin'] == ''): 
            data['errorMsg'] = 'Request is not valid'
        elif verifyUser(request):
            user = CustomUser.objects.get(email = request.data['email'].strip(), name = request.data['userName'])
            if user.security_pin is not None:
                isValidPin = check_password(request.data['oldPin'], user.security_pin)
                if isValidPin:
                    user.security_pin = make_password(request.data['newPin'])
                    user.save()
                    data['isSuccess'] = True
                else:
                    data['errorMsg'] = 'Old pin is incorrect'
            
    except Exception as e:
        data['errorMsg'] = e.args

    return JsonResponse(data)


# print(make_password('1234'))
# print(check_password('1234', 'pbkdf2_sha256$600000$0FGnAqPynXqfu0MCTV69qi$w2MiZ7NwqilW2ZpWD0UQS3U9Rs0NTDhowYN0+BW9WBC='))

# LOG IN WITH PASSWORD
@api_view(['POST'])
def api_login(request):
    data = {}
    data['isSuccess'] = False
    data['errorMsg'] = ''
    user = ''
    data['otpConfirm'] = False
    data['security_pin'] = False
    data['acctBal'] = '0' # IN CASE OF NEW USER THAT DOES NOT HAVE ACCT HISTORY
    try:
        if request.data['email'] is None or request.data['email'] == '' or request.data['password'] is None or request.data['password'] == '': 
            data['errorMsg'] = 'Email or password is empty.'
        else:
            user = authenticate(request, email=request.data['email'].strip(), password=request.data['password'])
            if user is not None:
                login(request, user)
                print('ACCOUNT BAL 1: ' + str (data['acctBal']))
                acctBal = AccountHistory.objects.filter(customer=user).order_by('-created_date_time')
                for acctBa in acctBal:
                    data['acctBal'] = str (acctBa.closing_bal)
                    break
                print('ACCOUNT BAL 2: ' + str (data['acctBal']))
                data['token'] = Token.objects.get(user=user.id).key
                data['name'] = user.name
                if user.otpConfirm:
                    data['otpConfirm'] = True
                if user.security_pin is not None:
                    data['security_pin'] = True
                data['email'] = user.email
                data['mobile'] = user.mobile_no
                data['serverProfileImg'] = 'http://192.168.100.88:8000'+user.imageURL
                data['isSuccess'] = True
            else:
                data['errorMsg'] = 'Email or password is incorrect'
    except Exception as e:
        data['errorMsg'] = e.args

    return JsonResponse(data)



# CHANGE LOG IN PASSWORD
@api_view(['POST'])
def api_changePassword(request):
    data = {}
    data['isSuccess'] = False
    data['errorMsg'] = ''
    try:
        user = CustomUser.objects.get(email = request.data['email'].strip(), name = request.data['userName'])
        form = PasswordChangeForm(data= request.data, user= user)

        if form.is_valid():
            user = form.save()
            # update_session_auth_hash(request.data, user)  # Important! Otherwise the user’s auth session will be invalidated and she/he will have to log in again.
            print('FORM IS VALID')
            data['isSuccess'] = True
        else:
            
            print('FORM IS INVALID')
            data['errorMsg'] = form.error_messages
    except Exception as e:
        data['errorMsg'] = e.args

    return JsonResponse(data, safe=False)


# LOG IN WITH PIN
@api_view(['POST'])
def api_login_with_pin(request):
    data = {}
    data['isSuccess'] = False
    data['errorMsg'] = ''
    user = ''
    isValidPin = False
    data['otpConfirm'] = False
    data['security_pin'] = False
    data['acctBal'] = '0' # IN CASE OF NEW USER THAT DOES NOT HAVE ACCT HISTORY
    
    try:
        if (request.data['email'] is None or request.data['email'] == '') and (request.data['userName'] is None or request.data['userName'] == '') and (request.data['pin'] is None or request.data['pin'] == ''): 
            data['errorMsg'] = "Kindly click on the 'Log in' to use your email and password. "
        else:
            user = CustomUser.objects.get(email = request.data['email'].strip(), name = request.data['userName'])
            isValidPin = check_password(request.data['pin'], user.security_pin)
            if isValidPin:

                login(request, user)
                acctBal = AccountHistory.objects.filter(customer=user).order_by('-created_date_time')
                for acctBa in acctBal:
                    data['acctBal'] = str (acctBa.closing_bal)
                    print(data['acctBal'])
                    break
                data['token'] = Token.objects.get(user=user.id).key
                data['name'] = user.name
                if user.otpConfirm:
                    data['otpConfirm'] = True
                if user.security_pin is not None:
                    data['security_pin'] = True
                data['email'] = user.email
                data['mobile'] = user.mobile_no
                data['isSuccess'] = True
            else:
                logout(request)
                data['errorMsg'] = 'Pin is incorrect'
    except Exception as e:
        data['errorMsg'] = "Kindly click on the 'Log in' to use your email and password."

    return JsonResponse(data)


@api_view(['POST'])
def api_logoutUser(request):
    data = {}
    data['isSuccess'] = False
    try:
        logout(request)
        data['isSuccess'] = True
    except Exception as e:
        data['errorMsg'] = e.args
    return JsonResponse(data, safe=False)


@api_view(['POST'])
def api_deactivateAccount(request):
    data = {}
    data['isSuccess'] = False
    data['errorMsg'] = ''
    try:
        if verifyUser(request):
            user = authenticate(request, email=request.data['email'].strip(), password=request.data['password'])
            if user is not None:
                logout(request)
                # AT THE POINT OF DELETING THE CUSTOMER ACCT, IF A REFERRAL
                # WAS CREATED, DELETE THE RECORD
                refer = Referral.objects.filter(referred_cus = user.id)
                for ref in refer:
                    ref.delete()
                user.delete()
                # user.is_deactivateAcct = True
                # user.save()
                data['isSuccess'] = True
            else:
                data['errorMsg'] = 'Incorrect password!'
    except Exception as e:
        data['errorMsg'] = e.args
    
    return JsonResponse(data, safe=False)


@api_view(['GET'])
def api_dataSubscription(request):
    data = {}
    data['isSuccess'] = False
    data['errorMsg'] = ''
    try:
        if verifyUser(request):
            dataSubscription = DataSubscription.objects.filter(active=True)
            data['dataSubList'] = toJsonDataSub(dataSubscription)
            data['isSuccess'] = True
        else:
            logout(request)
            data['errorMsg'] = 'Account is not verified'
    except Exception as e:
        data['errorMsg'] = e.args

    return JsonResponse(data)


@api_view(['POST'])
def api_set_updateAcct(request):
    data = {}
    data['isSuccess'] = False
    requestCall = ''
    try:
        if verifyUser(request):
            # ADD/UPDATE IMAGE FILE
            if request.FILES.get("image", None) is not None:
                acctProfile = CustomUser.objects.get(id=request.user.id)
                # CALL THIS FUNCTION TO REMOVE THE EXISTING IMAGE FROM
                # THE IMAGE FOLDER BEFORE SAVING THE NEW ONE
                removeImageFile(acctProfile, '')
                acctProfile.image = request.FILES.get('image')
                acctProfile.save()
                
                data['isSuccess'] = True
                return JsonResponse(data, safe=False)
            
            # REQUEST TO DELETE PROFILE PHOTO
            elif(request.data.get('call')):
                requestCall = request.data.get('call')
                if (requestCall != '' and requestCall == 'removeProfilePhoto'):
                    acctProfile = CustomUser.objects.get(id=request.user.id)
                    # CALL THIS FUNCTION TO REMOVE THE EXISTING IMAGE FROM
                    # THE IMAGE FOLDER
                    removeImageFile(acctProfile, '')
                    acctProfile.image = ''
                    acctProfile.save()

                    data['isBalVisible'] = acctProfile.is_balance_visible
                    data['isSuccess'] = True
                    return JsonResponse(data, safe=False)

                # REQUEST CALL TO TOGGLE ACCOUNT BALANCE
                elif (requestCall != '' and requestCall == 'toggleAcctBal'):
                    acctProfile = CustomUser.objects.get(id=request.user.id)
                    if (request.data.get('isShowAcctBal') == True):
                        print('enter1')
                        acctProfile.is_balance_visible = False
                    elif (request.data.get('isShowAcctBal') == False):
                        print('enter2')
                        acctProfile.is_balance_visible = True
                    acctProfile.save()
                    data = {
                        'image': config('URL_ENDPOINT')+acctProfile.imageURL,
                        'isBalVisible': acctProfile.is_balance_visible,
                        'name': acctProfile.name,
                        'mobile': acctProfile.mobile_no,
                        'isSuccess': True
                    }
                    return JsonResponse(data, safe=False)
                
                # REQUEST TO UPDATE NAME AND MOBILE
                elif (requestCall != '' and requestCall == 'editNameMobile'):
                    acctProfile = CustomUser.objects.get(id=request.user.id)
                    acctProfile.name = request.data.get('name')
                    acctProfile.mobile_no = request.data.get('mobile').replace(" ", "")
                    acctProfile.save()
                    data = {
                        'image': config('URL_ENDPOINT')+acctProfile.imageURL,
                        'isBalVisible': acctProfile.is_balance_visible,
                        'name': acctProfile.name,
                        'mobile': acctProfile.mobile_no,
                        'isSuccess': True
                    }
                    return JsonResponse(data, safe=False)

                # REQUEST TO UPDATE ACCOUNT STATUS
                elif (requestCall != '' and requestCall == 'requestAcctStatus'):
                    acctProfile = CustomUser.objects.get(id=request.user.id)
                    acctProfile.is_active = request.data.get('is_activeAcct')
                    acctProfile.save()
                    data = {
                        'image': config('URL_ENDPOINT')+acctProfile.imageURL,
                        'isBalVisible': acctProfile.is_balance_visible,
                        'name': acctProfile.name,
                        'mobile': acctProfile.mobile_no,
                        'is_activeAcct': acctProfile.is_active,
                        'isSuccess': True
                    }
                    return JsonResponse(data, safe=False)
                
                # REQUEST TO AUTHORIZE EVERY TRANSACTION
                elif (requestCall != '' and requestCall == 'authorizeTransactions'):
                    acctProfile = CustomUser.objects.get(id=request.user.id)
                    acctProfile.authorize_all_trans = request.data.get('isAuthorizeTrans')
                    
                    acctProfile.save()
                    data = {
                        'isBalVisible': acctProfile.is_balance_visible,
                        'isAuthorizeTrans': acctProfile.authorize_all_trans,
                        'isSuccess': True
                    }
                elif (requestCall != '' and requestCall == 'lifeCycleState'):
                    acctProfile = CustomUser.objects.get(id=request.user.id)
                    if (request.data.get('isLifeCycleState') == True):
                        print('enter1')
                        acctProfile.is_lock_inactive_mode = False
                    elif (request.data.get('isLifeCycleState') == False):
                        print('enter2')
                        acctProfile.is_lock_inactive_mode = True
                    acctProfile.save()
                    data = {
                        'image': config('URL_ENDPOINT')+acctProfile.imageURL,
                        'isBalVisible': acctProfile.is_balance_visible,
                        'name': acctProfile.name,
                        'mobile': acctProfile.mobile_no,
                        'isSuccess': True,
                        'isLifeCycleState': acctProfile.is_lock_inactive_mode,
                    }
                    return JsonResponse(data, safe=False)
        else:
            logout(request)
    except Exception as e:
        data['errorMsg'] = e.args
    return JsonResponse(data, safe=False)


# FUNCTION TO REMOVE IMAGE FILE FROM APPLICATION FOLDER
def removeImageFile(acctProfile, value):
    print(value)
    if not value:
        try:
            os.remove(acctProfile.image.path)
        except:
            pass
    return value


def getSubscription(subId):
    sub = ''
    if (subId is not None):
        subscription = DataSubscription.objects.get(id=subId.id)
        sub = subscription.name
    return sub

# print(datetime.now().strftime("%Y-%m-%d"))
def customTimeFormat(dateTime):
    customDateTime = dateTime + timedelta(hours=1)
    customDateTime = customDateTime.strftime("%d, %b, %y")

    return customDateTime

    
@api_view(['POST'])
def api_getProfileInfo(request):
    data = {}
    data['isSuccess'] = False
    data['errorMsg'] = ''
    try:
        if verifyUser(request):
            acctProfile = CustomUser.objects.get(id=request.user.id)
            
            data['userProfile'] = {
                'image': config('URL_ENDPOINT')+acctProfile.imageURL,
                'isBalVisible': acctProfile.is_balance_visible,
                'name': acctProfile.name,
                'is_activeAcct': acctProfile.is_active,
                'data_default_no': acctProfile.data_default_no,
                'airtime_default_no': acctProfile.airtime_default_no,
                'cable_iuc_default': acctProfile.cable_iuc_default,
                'internet_default_no': acctProfile.internet_default_no,
                'meter_default_no': acctProfile.meter_default_no,
                'authorize_all_trans': acctProfile.authorize_all_trans,
                'is_lock_inactive_mode': acctProfile.is_lock_inactive_mode,
                'unique_referral_code': acctProfile.unique_referral_code,
                # 'isSuccess': True
            }
            transLog = TransactionLog.objects.filter(customer=acctProfile).order_by('-created_date_time')
            _transLog = []
            _counter = 0
            for tranLog in transLog:
                if (_counter == 15):
                    break
                record = {
                    'id': tranLog.id,
                    'transactionNo': tranLog.transaction_no,
                    'amount': tranLog.amount,
                    'dataAmt': tranLog.data_amt,
                    'createdDate': customTimeFormat(tranLog.created_date),
                    'subscription': getSubscription(tranLog.subscription),
                    'status': tranLog.status,
                    'serviceCode': tranLog.service_code,
                    'serviceProvided': tranLog.service_provided
                }
                _transLog.append(record)
                _counter += 1
            data['tranLog'] = _transLog

            # GET USER AGREEMENT RECORD
            compInfo = CompanyInfo.objects.get(id = 1)
            data['compAgreement'] = {'compAgreementRecord': compInfo.user_agreement}
            data['isSuccess'] = True
            return JsonResponse(data, safe=False)
        else:
            logout(request)
            data['errorMsg'] = 'Account is not verified'
    except Exception as e:
        data['errorMsg'] = e.args

    return JsonResponse(data, safe=False)


# GETTING THE PROFILE PICTURE. THIS IS USED TO DISPLAY THE PROFILE
# PICTURE WHEN THE USER IS ASKED TO LOG IN WITH PIN.
@api_view(['POST'])
def api_acctProfilePix(request):
    data = {}
    data['isSuccess'] = False
    data['errorMsg'] = ''
    try:
        user = CustomUser.objects.get(email = request.data['email'].strip())
        data = {'image':config('URL_ENDPOINT')+user.imageURL,} 
        data['isSuccess'] = True
    except Exception as e:
        data['errorMsg'] = "Kindly click on the 'Log in' to use your email and password."

    return JsonResponse(data, safe=False)


# REQUEST TO GET TOKEN VIA EMAIL AND USERNAME.
# BIOMETRIC WAS USED TO LOGIN
@api_view(['POST'])
def api_authenticateWithBiometrics(request):
    data = {}
    data['isSuccess'] = False
    data['errorMsg'] = ''
    data['acctBal'] = '0' # IN CASE OF NEW USER THAT DOES NOT HAVE ACCT HISTORY
    try:
        user = CustomUser.objects.get(email = request.data['email'].strip(), name = request.data['userName'])
        
        if verifyUser2(user):

            user = CustomUser.objects.get(email = request.data['email'].strip(), name = request.data['userName'])
           
            login(request, user)
            acctBal = AccountHistory.objects.filter(customer=user).order_by('-created_date_time')
            for acctBa in acctBal:
                data['acctBal'] = str (acctBa.closing_bal)
                break
            data['token'] = Token.objects.get(user=user.id).key
            data['name'] = user.name
            data['email'] = user.email
            data['mobile'] = user.mobile_no
            data['isSuccess'] = True
                
        else:
            data['errorMsg'] = 'Account is not verified'
    except Exception as e:
        data['errorMsg'] = "Kindly click on the 'Log in' to use your email and password."

    return JsonResponse(data, safe=False)


# REQUEST TO PERFORM TRANSACTION
@api_view(['POST'])
def api_processTransaction(request):
    data = {}
    data['isSuccess'] = False
    data['errorMsg'] = ''
    try:
        user = CustomUser.objects.get(email = request.data['email'].strip(), name = request.data['userName'])
        # CHECKING IF PIN AUTHORIZATION IS REQUIRED TO PERFORM TRANSACTION
        if (user.authorize_all_trans):
            # CHECKING IF PIN IS CORRECT
            isValidPin = check_password(request.data['pin'], user.security_pin)
            if isValidPin:
                acctHistory = AccountHistory.objects.filter(customer=user)
                acctBal = ''
                # GET THE USER'S CURRENT ACCT BALANCE
                for acct in acctHistory:
                    acctBal = acct.getClosingBal()
                    print('NEW ACCT BAL: ', acctBal)
                    break
                if (verifyUser2(user)):
                    resp = serviceTransaction(request, acctBal)
                    if (resp['isPass']):
                        data['closingBal'] = str (resp['closingBal'])
                        data['isSuccess'] = True
                    else:
                        data['errorMsg'] = resp['errorMessage']
                else:
                    data['errorMsg'] = 'User account could not be verified'
            else:
                data['errorMsg'] = 'Invalid pin'
        # PERFORM TRANSACTION WITHOUT PIN AUTHORIZATION
        else:
            acctHistory = AccountHistory.objects.filter(customer=user)
            acctBal = ''
            # GET THE USER'S CURRENT ACCT BALANCE
            for acct in acctHistory:
                acctBal = acct.getClosingBal()
                break
            if (verifyUser2(user)):
                resp = serviceTransaction(request, acctBal)
                if (resp['isPass']):
                    data['closingBal'] = str (resp['closingBal'])
                    data['isSuccess'] = True
                else:
                    data['errorMsg'] = resp['errorMessage']
            else:
                data['errorMsg'] = 'User account could not be verified'
            
    except Exception as e:
        data['errorMsg'] = e.args
    
    return JsonResponse(data, safe=False)


# REQUEST TO GET TRANSACTION LOG
@api_view(['POST'])
def api_acctTransactionLog(request):
    data = {}
    data['isSuccess'] = False
    data['errorMsg'] = ''

    try:
        if verifyUser(request):
            acctProfile = CustomUser.objects.get(id=request.user.id)
            transLog = TransactionLog.objects.filter(customer=acctProfile).order_by('-created_date_time')
            recordLog = []
            for trans in transLog:
                
                record = {
                    'id': trans.id,
                    'subscription': getSubscription(trans.subscription),
                    'transactionNo': trans.transaction_no,
                    'amount': trans.amount,
                    'dataAmt': trans.data_amt,
                    'createdDate': customTimeFormat(trans.created_date),
                    'status': trans.status,
                    'serviceCode': trans.service_code,
                    'serviceProvided': trans.service_provided
                }
                recordLog.append(record)
            data['transLog'] = recordLog
            
            data['isSuccess'] = True
    except Exception as e:
        data['errorMsg'] = e.args
    
    return JsonResponse(data, safe=False)


# REQUEST TO GET ACCOUNT STATMENT
@api_view(['POST'])
def api_acctStatement(request):
    data = {}
    data['isSuccess'] = False
    data['errorMsg'] = ''
    data['openBal'] = 0
    isOpenBal = True
    try:
        if verifyUser(request):
            acctProfile = CustomUser.objects.get(id=request.user.id)
            acctHistory = AccountHistory.objects.filter(customer=acctProfile, transaction_date__range=[str (request.data['startDate']), str (request.data['endDate'])])
            compInfo = CompanyInfo.objects.get(id = 1) # COMPANY INFO WILL BE USED ON THE PDF
            recordLog = []
            
            for accts in acctHistory:
                if isOpenBal:
                    data['openBal'] = accts.closing_bal + accts.debit
                    isOpenBal = False

                record = {
                    'id': accts.id,
                    'transactionDate': customTimeFormat(accts.transaction_date),
                    'description': accts.description,
                    'credit': accts.credit,
                    'debit': accts.debit,
                    'closingBal': accts.closing_bal,
                    'status': accts.status,
                }
                recordLog.append(record)
            data['acctStatement'] = recordLog

            # COMPANY INFO WILL BE USED IN PDF TEMPLATE
            data['compInfo'] = {
                'businessName': compInfo.business_name,
                'streetAddress1': compInfo.street_address1,
                'city': compInfo.city,
                'state': compInfo.state,
                'postal': compInfo.postal,
                'country': compInfo.country,
                'phone': compInfo.phone,
                'phone2': compInfo.phone2,
                'email': compInfo.email,
                'companyLogo': 'http://192.168.100.88:8000'+compInfo.imageURL,
            }
            data['isSuccess'] = True
    except Exception as e:
        data['errorMsg'] = e.args
    
    return JsonResponse(data, safe=False)


# REQUEST TO CREDIT CUSTOMER WALLET
@api_view(['POST'])
def api_creditCusWallet(request):
    data = {}
    data['isSuccess'] = False
    data['errorMsg'] = ''
    data['openBal'] = 0
    try:
        if verifyUser(request):
            acctProfile = CustomUser.objects.get(id=request.user.id)
            acct = AccountHistory.objects.create(
                customer = acctProfile,
                refPay = request.data['ref'],
                status = request.data['status'],
            )
            status, result = verify_payment(request, acct.refPay)
            if status:
                if float (result['amount'] / 100) == float (request.data['credit']):
                    acct.payVerify = True
                acct.credit = float (request.data['credit'])
                acct.payMethod = result['channel']
                acct.description = result['reference']
                acct.bank = result['authorization']['bank']
                acct.payCard = result['authorization']['card_type']
                acct.save()

                if Referral.objects.filter(referred_cus = acctProfile.id).exists():
                    ref = Referral.objects.get(referred_cus = acctProfile.id)
                    if ref.referred_cus_initial_deposit > 0:
                        pass
                    else:
                        ref.referred_cus_initial_deposit = acct.credit
                        ref.is_payment_verified = acct.payVerify
                        ref.bonus_amt = (acct.credit / 100) * ref.percentage_rate
                        if acct.payVerify:
                            ref.referral_process = 'Transfer'
                        else:
                            ref.referral_process = 'Pending'
                        ref.save()
                
            data['amt'] = acct.credit
            data['isSuccess'] = True
    except Exception as e:
        data['errorMsg'] = e.args
    
    return JsonResponse(data, safe=False)


def verify_payment(request: HttpRequest, ref: str):
    acct = AccountHistory.objects.get(refPay=ref)
    status, result = acct.verify_payment()
    # if verified:
    #     messages.success(request, "Verification successful")
    # else:
    #     messages.error(request, "Verification Failed")
    return status, result


@api_view(['POST'])
def api_referrals(request):
    data = {}
    data['isSuccess'] = False
    data['errorMsg'] = ''
    try:
        print(request.data.get('call'))
        if verifyUser(request):
            user = CustomUser.objects.get(email=request.data['email'].strip())
            if request.data.get('call') == 'getReferral':
                ref = Referral.objects.filter(referral_customer = user).order_by('-created_date_time')
                jsonRef = convertReferralToJsonRecord(ref)
                data['jsonRef'] = jsonRef
                data['isSuccess'] = True
            elif request.data.get('call') == 'updateReferral':
                _ref = Referral.objects.get(id = request.data['val'])
                _ref.is_referral_process_complete = True
                _ref.referral_process = 'Complete'
                _ref.save()
                
                # CREDIT THE CUSTOMER'S ACCT WITH THE BONUS AMT.
                AccountHistory.objects.create(
                    customer = user,
                    refPay = 'RefBonus'+str(uuid.uuid4().time_low)[:4],
                    status = True,
                    payVerify = True,
                    credit = _ref.bonus_amt,
                    payMethod = 'Internal transfer',
                    description = 'Transfer request from referral bonus'
                )
                _ref = Referral.objects.filter(referral_customer = user).order_by('-created_date_time')
                data['isSuccess'] = True
                data['updatedRef'] = convertReferralToJsonRecord (_ref)
        else:
            data['errorMsg'] = 'User not verified'
    except Exception as e:
        data['errorMsg'] = e.args
    
    return JsonResponse(data, safe=False)



