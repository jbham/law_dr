import boto3
from typing import List, Optional
from app import crud

from app.db_models.business import Business


def get_multi(db_session, *, skip=0, limit=100, user_details=None) -> List[Optional[Business]]:
    return db_session.query(Business).offset(skip).limit(limit).all()


def get_by_business_name(db_session, *, full_name: str) -> Optional[Business]:
    return db_session.query(Business).filter(Business.full_name == full_name).first()


def create(db_session, main_admin, *, business_in: Business) -> Business:

    business = Business(
        full_name=business_in.full_name,
        created_by=business_in.created_by,
        modified_by=business_in.modified_by
    )
    db_session.add(business)
    db_session.commit()
    db_session.refresh(business)

    # create user pool
    user_pool = create_user_pool(business.id)

    # create user pool client
    user_pool_client = create_user_pool_client(user_pool["UserPool"]["Id"], business.id)

    # create main admin in Cognito
    crud.user.create_main_admin(db_session, user_to_create=main_admin, current_user=None,
                                pool_id=user_pool["UserPool"]["Id"])

    # update business with user pool details
    db_session.query(Business).filter_by(id=business.id)\
        .update({Business.user_pool_arn: user_pool["UserPool"]["Arn"],
                 Business.user_pool_id: user_pool["UserPool"]["Id"],
                 Business.user_pool_name: user_pool["UserPool"]["Name"],
                 Business.user_pool_created_date: user_pool["UserPool"]["CreationDate"],
                 Business.user_pool_modified_date: user_pool["UserPool"]["LastModifiedDate"]})

    db_session.commit()
    return business


def create_user_pool(business_id):
    client = boto3.client('cognito-idp')
    response = client.create_user_pool(
        PoolName=f'User_Pool_{business_id}',
        Policies={
            'PasswordPolicy': {
                'MinimumLength': 8,
                'RequireUppercase': True,
                'RequireLowercase': True,
                'RequireNumbers': True,
                'RequireSymbols': True,
                'TemporaryPasswordValidityDays': 1
            }
        },
        # LambdaConfig={
        #     'PreSignUp': 'string',
        #     'CustomMessage': 'string',
        #     'PostConfirmation': 'string',
        #     'PreAuthentication': 'string',
        #     'PostAuthentication': 'string',
        #     'DefineAuthChallenge': 'string',
        #     'CreateAuthChallenge': 'string',
        #     'VerifyAuthChallengeResponse': 'string',
        #     'PreTokenGeneration': 'string',
        #     'UserMigration': 'string'
        # },
        AutoVerifiedAttributes=[
            'email',
        ],
        # AliasAttributes=[
        #     'email',
        # ],
        UsernameAttributes=[
            'email',
        ],
        # SmsVerificationMessage='string',
        # EmailVerificationMessage='string',
        # EmailVerificationSubject='string',
        VerificationMessageTemplate={
            # 'SmsMessage': 'string',
            # 'EmailMessage': 'string',
            # 'EmailSubject': 'string',
            # 'EmailMessageByLink': 'string',
            # 'EmailSubjectByLink': 'string',
            'DefaultEmailOption': 'CONFIRM_WITH_LINK'
        },
        # SmsAuthenticationMessage='string',
        # MfaConfiguration='OFF' | 'ON' | 'OPTIONAL',
        # DeviceConfiguration={
        #     'ChallengeRequiredOnNewDevice': True | False,
        #     'DeviceOnlyRememberedOnUserPrompt': True | False
        # },
        EmailConfiguration={
            # 'SourceArn': 'string',
            # 'ReplyToEmailAddress': 'string',
            'EmailSendingAccount': 'COGNITO_DEFAULT'
        },
        # SmsConfiguration={
        #     'SnsCallerArn': 'string',
        #     'ExternalId': 'string'
        # },
        # UserPoolTags={
        #     'string': 'string'
        # },
        AdminCreateUserConfig={
            'AllowAdminCreateUserOnly': True,
            # 'UnusedAccountValidityDays': 123,
            # 'InviteMessageTemplate': {
            #     # 'SMSMessage': 'string',
            #     'EmailMessage': 'string',
            #     'EmailSubject': 'string'
            # }
        },
        # Schema=[
        #     {
        #         'Name': 'string',
        #         'AttributeDataType': 'String' | 'Number' | 'DateTime' | 'Boolean',
        #         'DeveloperOnlyAttribute': True | False,
        #         'Mutable': True | False,
        #         'Required': True | False,
        #         'NumberAttributeConstraints': {
        #             'MinValue': 'string',
        #             'MaxValue': 'string'
        #         },
        #         'StringAttributeConstraints': {
        #             'MinLength': 'string',
        #             'MaxLength': 'string'
        #         }
        #     },
        # ],
        # UserPoolAddOns={
        #     'AdvancedSecurityMode': 'OFF' | 'AUDIT' | 'ENFORCED'
        # }
    )

    print(response)

    return response


def create_user_pool_client(user_pool_id, business_id):
    client = boto3.client('cognito-idp')
    response = client.create_user_pool_client(
        UserPoolId=user_pool_id,
        ClientName=f"client_name_{business_id}",
        GenerateSecret=True,
        RefreshTokenValidity=1,
        # ReadAttributes=[
        #     'string',
        # ],
        # WriteAttributes=[
        #     'string',
        # ],
        ExplicitAuthFlows=[
            'USER_PASSWORD_AUTH',
        ],
        # SupportedIdentityProviders=[
        #     'string',
        # ],
        # CallbackURLs=[
        #     'string',
        # ],
        # LogoutURLs=[
        #     'string',
        # ],
        # DefaultRedirectURI='string',
        # AllowedOAuthFlows=[
        #     'code' | 'implicit' | 'client_credentials',
        # ],
        # AllowedOAuthScopes=[
        #     'string',
        # ],
        # AllowedOAuthFlowsUserPoolClient=True | False,
        # AnalyticsConfiguration={
        #     'ApplicationId': 'string',
        #     'RoleArn': 'string',
        #     'ExternalId': 'string',
        #     'UserDataShared': True | False
        # }
    )

    return response
