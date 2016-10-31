import os

def skip_dicsovery_url(value, skip_str='https://discovery.etcd.io'):
    # split into lines (keep '\n')
    v = value.splitlines(True)
    # remove skip_str line from list
    v = [x for x in v if skip_str not in x]
    # compare two lists
    return ''.join(v)

def ec2_instance_info(value, return_key):
    # collect results from aws ec2 describe-instances result
    results = []
    for reservation in value['Reservations']:
      for instance in reservation['Instances']:
         results.append(instance[return_key])

    return results

def get_subnets(value, tag_key, tag_value, return_key='id'):
    # return an attribute for all subnets that match
    subnets = []
    for item in value:
      for key, value in item['resource_tags'].iteritems():
        if key == tag_key and value == tag_value:
          subnets.append(item[return_key])

    return subnets

def get_subnets_full(value, tag_key, tag_value):
    # return subnets that match
    subnets = []
    for item in value:
      for key, value in item['resource_tags'].iteritems():
        if key == tag_key and value == tag_value:
          subnets.append(item)

    return subnets

# parses "aws rds describe-db-instances --db-instance-identifier <id>" output to fetch the entdpoint - must be used with db-instance-identifier
def get_rds_endpoint(db_instance):
    return db_instance['DBInstances'][0]['Endpoint']['Address']

class FilterModule(object):
    ''' Ansible core jinja2 filters '''

    def filters(self):
        return {
            'ec2_instance_info': ec2_instance_info,
            'get_subnets': get_subnets,
            'get_subnets_full': get_subnets_full,
            'skip_dicsovery_url': skip_dicsovery_url,
            'get_rds_endpoint': get_rds_endpoint
        }
