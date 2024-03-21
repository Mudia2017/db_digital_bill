

from curses import savetty
from email import message
from time import time
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
import pyotp
from datetime import datetime, timedelta
from digital_billing_app.models import CustomUser, DataSubscription, TransactionLog, AccountHistory
import math
from decouple import config


# FUNCTION USED TO SEND OTP CODE TO USERS
def get_otp(request):
    totp = pyotp.TOTP(pyotp.random_base32(), interval=120, digits=5)
    otp = totp.now()
    # LET'S STORE THE KEY IN THE USER SESSION
    request.session['otp_secret_key'] = totp.secret
    # ADD 4 MINS TO THE CURRENT TIME AND STORE IN USER SESSION
    valid_date = datetime.now() + timedelta(minutes=2)
    request.session['otp_valid_date'] = str(valid_date)
    request.session['otp_code'] = otp

    # send_email_to_client(request.data['name'], request.data['email'], otp)
    return otp


# FUNCTION TO SEND EMAIL
def send_email_to_client(name, recipient_email, otp_code):
    template = render_to_string ('digital_billing_app/email_template.html', {
        'call': 'SendOTPCode', 'name': name, 'otp_code': otp_code
    })
    subject = "OTP Verification Code"
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [recipient_email]
    email = EmailMessage(subject, template, from_email, recipient_list)
    email.send()
    

def verifyUser(request):
    isVerified = False
    if request.user.security_pin and request.user.otpConfirm and request.user.is_authenticated and request.user.is_active:
        isVerified = True

    return isVerified

def verifyUser2(user):
    isVerified = False
    if user.security_pin and user.otpConfirm and user.is_authenticated and user.is_active:
        isVerified = True
    return isVerified

def toJsonDataSub(dataSub):
    dataSubs = []
   
    for _dataSub in dataSub:
        dataRec = {
            'id': _dataSub.id,
            'name': _dataSub.name,
            'code': _dataSub.code,
            'amount_mb': _dataSub.amount_mb,
            'price': _dataSub.price,
            'discount': _dataSub.discount
        }
        dataSubs.append(dataRec)
    
    return dataSubs




def dataInternetSub(request, user, acctBal):
    data = {}
    dataSub = DataSubscription.objects.get(id=request.data['subscriptionId'])
    # CHECKING THAT THE SUBSCRIPTION IS ACTIVE
    if (dataSub.active):
        # CHECKING THAT THE REQUESTED TRANSACTION AMT IS EQUAL TO DATA PRICE SUB
        # THIS IS TO ENSURE THAT THE USER DID NOT TEMPER WITH THE REQUESTED AMT
        if (request.data['requestedAmt'] == dataSub.price):
            # CHECKING THAT THE ACCT BAL IS EQUAL-TO OR GREATER THAN REQUESTED AMT
            if (float(acctBal) >= float (request.data['requestedAmt'])):
                currentTran = TransactionLog.objects.create(
                    customer=user,
                    subscription=dataSub,
                    transaction_no=request.data['mobileTransNo'],
                    service_code=request.data['providerChoice'],
                    service_provided=request.data['serviceProvided'],
                    service_fee=10,
                    amount=float (request.data['requestedAmt']),
                    data_amt=request.data['dataAmt'],
                    status=True
                )
                acct = AccountHistory.objects.create(
                    customer=user,
                    transaction_log=currentTran,
                    description=request.data['serviceProvided'],
                    debit=request.data['requestedAmt'],
                )

                print('Closing Bal: ', acct.getClosingBal())
                # AFTER PERFORMING THE TRANSACTION, GET THE CURRENT CLOSING BAL
                data['closingBal'] = acct.getClosingBal()
                
                data['isPass'] = True
            else:
                data['errorMessage'] = 'Insufficient account balance'
        else:
            data['errorMessage'] = 'Data price does not tally'
    else:
        data['errorMessage'] = 'Inactive plan selected'

    return data


# WE NEED TO CREATE THE SERVICE TRANSACTION
# CHECK THAT THE SERVICE REQUEST IS ACTIVE
def serviceTransaction(request, acctBal):
    data = {}
    data['isPass'] = False
    data['errorMessage'] = ''
    user = CustomUser.objects.get(email = request.data['email'].strip(), name = request.data['userName'])
    # EXECUTE THIS BLOCK IF REQUEST IS FROM AIRTIME SERVICE PROVIDER
    if (request.data['call'] == 'airtimeServiceProvider'):
        # CHECKING THAT THE ACCT BALANCE IS EQUAL-TO OR GREATER THAN REQUESTED TRANSACTION AMT
        if (float(acctBal) >= float (request.data['requestedAmt'])):
            
            currentTran = TransactionLog.objects.create(
                customer=user,
                transaction_no=request.data['mobileTransNo'],
                service_code=request.data['providerChoice'],
                service_provided=request.data['serviceProvided'],
                service_fee=10,
                amount=float (request.data['requestedAmt']),
                status=True
            )
            acct = AccountHistory.objects.create(
                customer=user,
                transaction_log=currentTran,
                description=request.data['serviceProvided'],
                debit=request.data['requestedAmt'],
            )

            print('Closing Bal: ', acct.getClosingBal())
            # AFTER PERFORMING THE TRANSACTION, GET THE CURRENT CLOSING BAL
            data['closingBal'] = acct.getClosingBal()
            # CHECKING IF THE TRANSACTION NUMBER WAS SET AS DEFAULT NUM
            # IF TRUE, SAVE THE TRAN. NUM TO THE DATABASE OF USER'S ACCT.
            # WHEN THE APP IS GETTING THE USER PROFILE, THIS NUM IS ALSO PULLED TO THE INTERFACE
            if (request.data['isNumSetAsDefault']):
                user.airtime_default_no = request.data['mobileTransNo']
                user.save()
            else:
                user.airtime_default_no = ''
                user.save()
            data['isPass'] = True
        else:
            data['errorMessage'] = 'Insufficient account balance'
  
    elif (request.data['call'] == 'dataServiceProvider'):
        data = dataInternetSub(request, user, acctBal)
        if (data['isPass']):
            # CHECKING IF THE TRANSACTION NUMBER WAS SET AS DEFAULT NUM
            # IF TRUE, SAVE THE TRAN. NUM TO THE DATABASE OF USER'S ACCT.
            # WHEN THE APP IS GETTING THE USER PROFILE, THIS NUM IS ALSO PULLED TO THE INTERFACE
            if (request.data['isNumSetAsDefault']):
                user.data_default_no = request.data['mobileTransNo']
                user.save()
            else:
                user.data_default_no = ''
                user.save()
       
    elif (request.data['call'] == 'internetServiceProvider'):
        data = dataInternetSub(request, user, acctBal)
        if (data['isPass']):
            # CHECKING IF THE TRANSACTION NUMBER WAS SET AS DEFAULT NUM
            # IF TRUE, SAVE THE TRAN. NUM TO THE DATABASE OF USER'S ACCT.
            # WHEN THE APP IS GETTING THE USER PROFILE, THIS NUM IS ALSO PULLED TO THE INTERFACE
            if (request.data['isNumSetAsDefault']):
                user.internet_default_no = request.data['mobileTransNo']
                user.save()
            else:
                user.internet_default_no = ''
                user.save()

    elif (request.data['call'] == 'cableTvServiceProvider'):
        data = dataInternetSub(request, user, acctBal)
        if (data['isPass']):
            # CHECKING IF THE TRANSACTION NUMBER WAS SET AS DEFAULT NUM
            # IF TRUE, SAVE THE TRAN. NUM TO THE DATABASE OF USER'S ACCT.
            # WHEN THE APP IS GETTING THE USER PROFILE, THIS NUM IS ALSO PULLED TO THE INTERFACE
            if (request.data['isNumSetAsDefault']):
                user.cable_iuc_default = request.data['mobileTransNo']
                user.save()
            else:
                user.cable_iuc_default = ''
                user.save()            

    return data


def sendResetPasswordEmail(reset_password_token):
    forgot_password_token = "{}".format(reset_password_token.key)
    greetings = "Hi {}!".format(reset_password_token.user.name)

    email_html_content = "Hi Joe, Please use this token to reset your password. {}".format(forgot_password_token)

    print(email_html_content)
    # message = Mail(

    # )



def computeTimeDifference(dateTime):
   
    # ===========================================================================
    computeCurrentTime = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    computeStoreTime = dateTime.strftime("%Y/%m/%d %H:%M:%S")

    computeCurrentTime = datetime.strptime(computeCurrentTime, "%Y/%m/%d %H:%M:%S")
    computeStoreTime = datetime.strptime(computeStoreTime, "%Y/%m/%d %H:%M:%S")
    print(f'Current DayTime {computeCurrentTime}')
    print(f'Saved time {computeStoreTime}')
    timeDiff = computeCurrentTime - computeStoreTime
    timeDifference = ''
    print(f'Time diff {timeDiff}')
    if timeDiff.seconds < 86400 and timeDiff.days == 0:
        hrTimeDiff = int (timeDiff.seconds / 3600)
        minTimeDiff = int ((timeDiff.seconds - (hrTimeDiff * 3600)) / 60)
        secTimeDiff = int (timeDiff.seconds - ((minTimeDiff * 60) + (hrTimeDiff * 3600)))

        if (minTimeDiff < 1 and hrTimeDiff < 1):
            timeDifference = 'less than a minute ago'
            print(timeDifference)
        elif (minTimeDiff < 60 and hrTimeDiff < 1):
            if minTimeDiff == 1:
                timeDifference = f'{minTimeDiff} minute ago'
            else:
                timeDifference = f'{minTimeDiff} minutes ago'
            print(timeDifference)
        else:
            if hrTimeDiff == 1:
                timeDifference = f'{hrTimeDiff} Hour ago'
            else:
                timeDifference = f'{hrTimeDiff} Hours ago'
            print(timeDifference)
        
        print(f'Hr: {hrTimeDiff} min: {minTimeDiff} sec: {secTimeDiff}')
    elif timeDiff.seconds < 86400 and timeDiff.days < 8:
        if timeDiff.days == 1:
            timeDifference = f'{timeDiff.days} Day ago'
        else:
            timeDifference = f'{timeDiff.days} Days ago'
        print(timeDifference)
    elif timeDiff.days < 31:
        if int (timeDiff.days / 7) == 1:
            timeDifference = '1 Week ago'
        else:
            timeDifference = f'{int (timeDiff.days / 7)} Weeks ago'
        print(timeDifference)
    elif timeDiff.days < 366:
        if int (timeDiff.days / 30) == 1:
            timeDifference = '1 Month ago'
        else:
            timeDifference = f'{int (timeDiff.days / 30)} Months ago'
        print(timeDifference)
    else:
        if int (timeDiff.days / 365) == 1:
            yr = int (timeDiff.days / 365)
            modulo = math.modf(timeDiff.days / 365)
            mons = int ( (modulo[0] * 365) / 30)
            if mons < 1:
                timeDifference = f'{yr} Year ago'
            elif mons == 1:
                timeDifference = f'{yr} Year {mons} month ago'
            elif mons > 1:
                timeDifference = f'{yr} Year {mons} months ago'
        else:
            yrs = int (timeDiff.days / 365)
            modulo = math.modf(timeDiff.days / 365)
            mons = int ( (modulo[0] * 365) / 30)
            if mons < 1:
                timeDifference = f'{yrs} Years ago'
            elif mons == 1:
                timeDifference = f'{yrs} Years {mons} month ago'
            else:
                timeDifference = f'{yrs} Years {mons} months ago'
        print(timeDifference)
   
    return timeDifference

def convertReferralToJsonRecord(refs):
    data = []
    for ref in refs:
        referredCusRec = CustomUser.objects.get(id = ref.referred_cus)
        record = {
            'id': ref.id,
            'profileImg': config('URL_ENDPOINT')+referredCusRec.imageURL,
            'referredCusName': referredCusRec.name,
            'referred_cus_initial_deposit': ref.referred_cus_initial_deposit,
            'is_payment_verified': ref.is_payment_verified,
            'bonus_amt': ref.bonus_amt,
            'referral_process': ref.referral_process,
            'is_referral_process_complete': ref.is_referral_process_complete,
            'created_date_time': computeTimeDifference (ref.created_date_time)
        }
        data.append(record)
    return data



