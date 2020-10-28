import boto3
import cfnresponse

def handler(event, context):

    try:

        the_event = event['RequestType']
        response_data = {}
        phy_res_id = str(hash(event['StackId']
                              + event['LogicalResourceId']))[1:]

        print("Event dump: %s" % str(event))
        print("Request type: ", str(the_event))

        if the_event in ('Create', 'Update'):

            unique_id = str(hash(event['StackId']))[1:11]
            print("Unique ID: %s ." % unique_id)
            response_data['unique_id'] = unique_id

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
