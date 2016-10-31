import pytest
from helpers import ec2_fingerprint_key

@pytest.fixture
def ec2():
    import boto3
    return boto3.resource('ec2')

@pytest.fixture
def session():
    import boto3
    return boto3.session.Session()

def get_fingerprints(ec2, session, ec2_key, local_key_file):
    # get registered keypair
    key_pair_info = ec2.KeyPair(ec2_key)
    # get fingerprint from local file
    fingerprint = ec2_fingerprint_key.get_private_rsa_fingerprint('/'.join(['keys', session.region_name, local_key_file]))
    # return tuple
    return (key_pair_info.key_fingerprint, fingerprint)

def test_bastion_keypair(ec2, session):
    f = get_fingerprints(ec2, session, 'bastion-keypair-dev', 'bastion-key-dev.pem')
    assert f[0] == f[1]

def test_coreos_keypair(ec2, session):
    f = get_fingerprints(ec2, session, 'coreos-keypair-dev', 'coreos-key-dev.pem')
    assert f[0] == f[1]

def test_etcd_keypair(ec2, session):
    f = get_fingerprints(ec2, session, 'etcd-keypair-dev', 'etcd-key-dev.pem')
    assert f[0] == f[1]
