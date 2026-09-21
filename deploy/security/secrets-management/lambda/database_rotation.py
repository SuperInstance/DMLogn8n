import json
import boto3
import secrets
import string
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """Secrets Manager Rotation Lambda for Database Credentials"""

    arn = event['SecretId']
    token = event['ClientRequestToken']
    step = event['Step']

    # Setup boto3 clients
    secrets_client = boto3.client('secretsmanager')
    rds_client = boto3.client('rds')

    # Get secret
    try:
        secret_value = secrets_client.get_secret_value(SecretId=arn, VersionStage='AWSCURRENT')
        secret = json.loads(secret_value['SecretString'])
    except Exception as e:
        logger.error(f"Error getting secret: {str(e)}")
        raise e

    if step == 'createSecret':
        create_secret(secrets_client, arn, token, secret)

    elif step == 'setSecret':
        set_secret(secrets_client, arn, token, secret, rds_client)

    elif step == 'testSecret':
        test_secret(secrets_client, arn, token, secret)

    elif step == 'finishSecret':
        finish_secret(secrets_client, arn, token)

    return {
        'statusCode': 200,
        'body': json.dumps('Secret rotation completed successfully')
    }

def create_secret(secrets_client, arn, token, secret):
    """Create a new secret"""
    try:
        # Check if secret already exists for this version
        secrets_client.get_secret_value(SecretId=arn, VersionId=token, VersionStage='AWSPENDING')
        logger.info("Secret already exists for version")
        return
    except secrets_client.exceptions.ResourceNotFoundException:
        # Generate new password
        new_password = generate_password()

        # Create new secret version
        new_secret = {
            'username': secret['username'],
            'password': new_password,
            'engine': secret['engine'],
            'host': secret['host'],
            'port': secret['port'],
            'dbname': secret['dbname']
        }

        secrets_client.put_secret_value(
            SecretId=arn,
            ClientRequestToken=token,
            SecretString=json.dumps(new_secret),
            VersionStages=['AWSPENDING']
        )

        logger.info("New secret created successfully")

def set_secret(secrets_client, arn, token, secret, rds_client):
    """Set the new password in RDS"""
    try:
        # Get pending secret
        pending_secret_value = secrets_client.get_secret_value(
            SecretId=arn,
            VersionId=token,
            VersionStage='AWSPENDING'
        )
        pending_secret = json.loads(pending_secret_value['SecretString'])

        # Update RDS user password
        try:
            rds_client.modify_db_instance(
                DBInstanceIdentifier=secret['host'].split('.')[0],
                MasterUserPassword=pending_secret['password'],
                ApplyImmediately=True
            )
            logger.info("RDS password updated successfully")
        except Exception as e:
            logger.error(f"Error updating RDS password: {str(e)}")
            raise e

    except Exception as e:
        logger.error(f"Error in set_secret: {str(e)}")
        raise e

def test_secret(secrets_client, arn, token, secret):
    """Test the new secret by connecting to the database"""
    import psycopg2

    try:
        # Get pending secret
        pending_secret_value = secrets_client.get_secret_value(
            SecretId=arn,
            VersionId=token,
            VersionStage='AWSPENDING'
        )
        pending_secret = json.loads(pending_secret_value['SecretString'])

        # Test database connection
        conn = psycopg2.connect(
            host=pending_secret['host'],
            port=pending_secret['port'],
            database=pending_secret['dbname'],
            user=pending_secret['username'],
            password=pending_secret['password']
        )

        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if result[0] == 1:
            logger.info("Database connection test successful")
        else:
            raise Exception("Database connection test failed")

    except Exception as e:
        logger.error(f"Error testing secret: {str(e)}")
        raise e

def finish_secret(secrets_client, arn, token):
    """Finish the rotation by moving the pending secret to current"""
    try:
        # Get current secret version
        current_version = secrets_client.describe_secret(SecretId=arn)

        # Remove AWSCURRENT from current version
        for version in current_version['VersionIdsToStages']:
            if 'AWSCURRENT' in current_version['VersionIdsToStages'][version]:
                secrets_client.update_secret_version_stage(
                    SecretId=arn,
                    VersionStage='AWSCURRENT',
                    MoveToVersionId=token,
                    RemoveFromVersionId=version
                )
                break

        logger.info("Secret rotation completed successfully")

    except Exception as e:
        logger.error(f"Error finishing secret rotation: {str(e)}")
        raise e

def generate_password(length=32):
    """Generate a secure password"""
    alphabet = string.ascii_letters + string.digits + "!#$%&()*+,-./:;<=>?@[]^_`{|}~"
    return ''.join(secrets.choice(alphabet) for _ in range(length))