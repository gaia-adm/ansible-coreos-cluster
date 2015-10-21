# ansible-coreos-cluster
Ansible playbook for EC2 Gaia infrastructure cluster setup.
The created infrastructure is inspired by great [A VPC Reference Architecture](http://blog.bwhaley.com/reference-vpc-architecture) post by Ben Whaley.

Core infrastructure principles:
- separate VPC, spanning multiple AZ, for every environment (production, testing, beta, etc)
- separate VPC, spanning multiple AZ, for Bastion environment
- VPC peering between Bastion VPC and environment VPC
- Bastion machines are accessible only through SSH
- public subnets on environment VPC: only LB and NAT machines

# setup environment

In order to run this playbook you need to have the following installed on your machine:
- Python 2.7.x
- pip - Python package manager
- pip modules:
  - ansible - Ansible tool
  - awscli - Amazon CLI for Python
  - boto - AWS libraries

Run following command to install required modules
```
pip install ansible awscli boto
```

You will need also to setup the following ENV variables:
```
export AWS_ACCESS_KEY_ID=A...XXX
export AWS_SECRET_ACCESS_KEY=5....XXXX
export AWS_DEFAULT_REGION='us-east-1'
export AWS_DEFAULT_AZ1='us-east-1a'
export AWS_DEFAULT_AZ2='us-east-1b'
export AWS_DEFAULT_AZ3='us-east-1d'
export AWS_DEFAULT_AZ4='us-east-1e'

```
> **Note**: protect your AWS access key and secret access key

Region needs to be set also in inventory/ec2.ini file

`ec2.py` script is used to setup Ansible [Dynamic Inventory](http://docs.ansible.com/ansible/intro_dynamic_inventory.html) for AWS EC2.

# Ansible modules from Ansible 2.0 branch

We use additional Ansible AWS modules `ec2_ami_find, ec2_vpc, ec2_vpc_peering*, ec2_vpc_route_table_facts` from Ansible 2.0, that are not available in Ansible 1.9x.

# create a new environment

The environment consists from dedicated VPC with several public and private subnets in different AWS availability zones. To configure number of subnets and cluster size, edit `group_vars/envs/production/*.yaml` files or create an additional configuration files, based on above files, with different values.
To invoke Ansible playbook with different configuration (`myenv`) use the following commands:

```
cp -r group_vars/envs/production group_vars/envs/myenv
vim group_vars/envs/myenv/*.yaml
./main.sh myenv mydns
```

where mydns is a subdomain name used for accessing the environment over web (http://mydomain.gaiahub.io)

For environment cleanup use the following command:
```
./clean.sh myenv mydns
```

