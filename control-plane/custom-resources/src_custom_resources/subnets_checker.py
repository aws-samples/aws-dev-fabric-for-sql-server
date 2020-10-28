import boto3
import cfnresponse

def error_and_exit(error):

    print(error)
    raise Exception(error)

def handler(event, context):

    try:

        the_event = event['RequestType']
        response_data = {}
        phy_res_id = str(hash(event['StackId']
                              + event['LogicalResourceId']))[1:]

        print("Event dump: %s" % str(event))
        print("Request type: ", str(the_event))

        if the_event in ('Create', 'Update'):

            input_subnet_list = event['ResourceProperties']['Subnets']
            the_vpc = event['ResourceProperties']['Vpc']
            input_count = event['ResourceProperties']['Input']
            print("Processing subnets: %s." % input_subnet_list)

            ec2 = boto3.client('ec2')

            if len(input_subnet_list) != int(input_count):

                error_and_exit("The amount of seleced subnets and the 'SelectedPrivateSubnetsCont' value differs.")

            print("Validating subnets and VPC ...")
            response = ec2.describe_subnets(Filters=[
                {
                    'Name': 'vpc-id',
                    'Values': [
                        the_vpc,
                    ]
                },
            ])

            vpc_subnets = list(map(lambda subnet:
                                   subnet['SubnetId'],
                                   response['Subnets']))

            if not all(subnet in vpc_subnets
                       for subnet in input_subnet_list):

                error_and_exit("All the subnets must belong to the "
                               + "same VPC [%s]." % the_vpc)

            print("[OK] Passed!")

            print("Validating subnets and AZs ...")
            az_s = []
            for sub in response['Subnets']:

                if sub['SubnetId'] in input_subnet_list:

                    if sub['AvailabilityZone'] not in az_s:

                        az_s.append(sub['AvailabilityZone'])

                    else:

                        error_and_exit("Only '1' Subnet per Availability Zone is allowed. You have at least (2) in AZ [%s]." % sub['AvailabilityZone'])

            print("[OK] Passed!")

            print("Validating that subnets are private ...")
            response = ec2.describe_route_tables(
                Filters=[
                    {
                        'Name': 'association.subnet-id',
                        'Values': input_subnet_list
                    },
                ])

            route_table_list = list(map(lambda route:
                                        route['Routes'],
                                        response['RouteTables']))

            for route in [r for sub_list in route_table_list
                          for r in sub_list]:

                gw_id = route.get('GatewayId', None)
                if gw_id and gw_id.startswith('igw-'):

                    error_and_exit("This setup does not allow public subnets. Please select only private subnets.")

            print("[OK] Passed!")

            print("Getting VPC CIDR ...")
            response_data['vpc_cidr'] = ec2.describe_vpcs(Filters=[
                {
                    'Name': 'vpc-id',
                    'Values': [
                        the_vpc,
                    ]
                },
            ])['Vpcs'][0]['CidrBlock']

            print("CIDR is: %s" % response_data['vpc_cidr'])

        print("Execution successful!")
        cfnresponse.send(event,
                         context,
                         cfnresponse.SUCCESS,
                         response_data,
                         physicalResourceId=phy_res_id)

    except Exception as e:

        print("Execution failed...")
        e_string = str(e)
        print(e_string)
        context.log_stream_name = e_string
        cfnresponse.send(event,
                         context,
                         cfnresponse.FAILED,
                         response_data,
                         physicalResourceId=phy_res_id)
