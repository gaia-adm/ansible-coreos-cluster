import pytest

@pytest.fixture
def ec2():
    import boto3
    return boto3.resource('ec2')

def test_bastion_vpc(ec2):
    vpcs = ec2.vpcs.filter(
        Filters=[
            { 'Name': 'state', 'Values': ['available'] },
            { 'Name': 'tag:Name', 'Values': ['bastion'] },
        ]
    )
    assert len(list(vpcs)) == 1, "failed to find 'bastion' VPC"
