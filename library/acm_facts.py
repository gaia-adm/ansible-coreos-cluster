#!/usr/bin/python
#
# This is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This Ansible library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: acm_facts
short_description: Gather facts about AWS ACM
description:
    - Gather facts about AWS ACM Certificates
version_added: "2.2"
author: "Alexei Ledenev (@alexeiled)"
options:
  region:
    description:
      - The AWS region to use.
    required: true
    aliases: ['aws_region', 'ec2_region']
  certificate_statuses:
    description:
      - The status or statuses on which to filter the list of ACM Certificates U(http://docs.aws.amazon.com/acm/latest/APIReference/API_ListCertificates.html) for possible statuses.
    required: false
    default: null
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Get all ACM certificates
- acm_facts:
    region: us-east-1

# Get all ISSUED ACM certificates with status
- acm_facts:
    region: us-east-1
    certificate_statuses: [ 'ISSUED' ]

'''

try:
    import botocore
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

def get_cert_info(cert):
    cert_info = { 'arn': cert['CertificateArn'],
                 'domain_name': cert['DomainName']
                }

    return cert_info

def list_certificates(client, module):

    certificate_statuses = module.params.get("certificate_statuses")
    cert_dict_array = []

    try:
        all_certs = client.list_certificates(CertificateStatuses=certificate_statuses)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Boto3 Client Error - " + str(e.msg))

    for cert in all_certs['CertificateSummaryList']:
        cert_dict_array.append(get_cert_info(cert))

    module.exit_json(certificates=cert_dict_array)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            certificate_statuses=dict(type='list', default=[]),
            region=dict(required=True, aliases=['aws_region', 'ec2_region']),
        )
    )

    module = AnsibleModule(argument_spec=argument_spec)

    # Validate Requirements
    if not HAS_BOTO3:
        module.fail_json(msg='botocore/boto3 is required.')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module, True)

    if region:
        try:
            client = boto3_conn(module=module, conn_type='client', resource='acm', region=region, **aws_connect_params)
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg="Boto3 Client Error - " + str(e.msg))
    else:
        module.fail_json(msg="region must be specified")

    list_certificates(client, module)

from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
