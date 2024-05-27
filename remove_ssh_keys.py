python
import boto3
import paramiko

# Connect to AWS Systems Manager
session = boto3.Session(profile_name='your_aws_profile')
ssm_client = session.client('ssm')

# Define the list of approved public keys
approved_public_keys = [
    'ssh-rsa AAAAB3Nz...approved_key1',
    'ssh-rsa AAAAB3Nz...approved_key2',
    # Add more approved public keys here
]

# Get a list of all managed instances
response = ssm_client.describe_instance_information()
instance_ids = [instance['InstanceId'] for instance in response['InstanceInformationList']]

# Iterate over each instance
for instance_id in instance_ids:
    try:
        # Start a Session Manager session
        response = ssm_client.start_session(Target=instance_id)
        session = response['Session']

        # Create a Session Manager plugin for paramiko
        plugin = paramiko.session.SessionManagerPlugin(
            ssm_client=ssm_client,
            session=session
        )

        # Create an SSH client using the Session Manager plugin
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.load_system_host_keys()
        ssh_client.connect(hostname=instance_id, sock=plugin.start())

        # Read the authorized_keys file
        stdin, stdout, stderr = ssh_client.exec_command('cat ~/.ssh/authorized_keys')
        authorized_keys = stdout.read().decode().split('\n')

        # Remove unapproved keys
        new_authorized_keys = [key for key in authorized_keys if key in approved_public_keys or not key]

        # Write the new authorized_keys file
        stdin, stdout, stderr = ssh_client.exec_command('echo "{}" > ~/.ssh/authorized_keys'.format('\n'.join(new_authorized_keys)))

        # Close the SSH client
        ssh_client.close()

    except Exception as e:
        print(f'Error processing instance {instance_id}: {e}')

print('SSH key cleanup completed.')