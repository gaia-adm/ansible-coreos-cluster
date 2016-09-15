import os

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


def get_hosted_zone_id(value):
    default_region=os.environ['AWS_DEFAULT_REGION']
    region_value=default_region.replace('-','_')+"_"
    print region_value
    for zone in value:
        print "Next zone: %s" % zone
        if zone.startswith(region_value):
            print "Selected: "+zone[len(region_value):]
            return zone[len(region_value):]

def has_volume_state(volume_info, state):
    return len(volume_info['Volumes']) == 1 and volume_info['Volumes'][0]['State'] == state

# parses "aws rds describe-db-instances --db-instance-identifier <id>" output to fetch the entdpoint - must be used with db-instance-identifier
def get_rds_endpoint(db_instance):
    return db_instance['DBInstances'][0]['Endpoint']['Address']

class FilterModule(object):
    ''' Ansible core jinja2 filters '''

    def filters(self):
        return {
            'ec2_instance_info': ec2_instance_info,
            'get_subnets': get_subnets,
            'get_dns_zone': get_dns_zone,
            'get_hosted_zone_id': get_hosted_zone_id,
            'has_volume_state': has_volume_state,
            'get_rds_endpoint': get_rds_endpoint
        }
