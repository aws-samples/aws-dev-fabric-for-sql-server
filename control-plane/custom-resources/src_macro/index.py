"""
## Macro transform ##

Creates N copies of CloudFormation resources, parametrising
them using a generated random ID.

Based on this AWS Sample macro: https://github.com/awslabs/aws-cloudformation-templates/tree/master/aws/services/CloudFormation/MacrosExamples/Count

"""
import copy
import json
from random import choice
from string import ascii_lowercase


def process_template(template, parameters):
    """Process the CloudFormation template.

    Parameters
    ----------
    template : JSON
        Input template that is going to be transformed.
    parameters : list
        Additional parameters for the processing.

    Returns
    -------
    type
        status (success|failed), processed template

    """
    new_template = copy.deepcopy(template)
    status = 'success'

    # Iterate over each of the CloudFormation created resources
    for name, resource in template['Resources'].items():

        # Check whether the current resource has the 'count' property
        if 'Count' in resource:

            try:
                ref_value = new_template['Resources'][name]['Count'].pop('Ref')
                # Convert referenced parameter to an integer value
                count = int(parameters[ref_value])
                # Remove the Count property from this resource
                new_template['Resources'][name].pop('Count')

            except AttributeError:
                # Use numeric count value
                count = new_template['Resources'][name].pop('Count')

            print("Found 'Count' property with value {} in '{}'"
                  "resource.... multiplying!".format(count, name))
            # Remove the original resource from the template
            # but preserve a local copy of it
            resourceToMultiply = new_template['Resources'].pop(name)
            # Create a new block of the resource multiplied with names
            # ending in the iterator and the placeholders substituted
            resourcesAfterMultiplication = multiply(name, resourceToMultiply, count)
            if not set(resourcesAfterMultiplication.keys()) & set(new_template['Resources'].keys()):
                new_template['Resources'].update(resourcesAfterMultiplication)
            else:
                status = 'failed'
                return status, template
        else:
            print("Did not find 'Count' property in"
                  "'{}' resource.... "
                  "Nothing to do!".format(name))

    return status, new_template


def update_placeholder(resource_structure, iteration):
    """Update/replace the placeholder in the resource.

    Parameters
    ----------
    resource_structure : type
        CloudFormation resource definition.
    iteration : integer
        Number of iteration.

    Returns
    -------
    type
        Modified CloudFormation resource

    """
    resource_string = json.dumps(resource_structure)
    place_holder_count = resource_string.count('%s')

    # If the placeholder is found then replace it
    if place_holder_count > 0:

        print("Found {} occurrences of string placeholder in JSON, replacing with iterator value {}".format(place_holder_count, iteration))

        # Generate a random string for replacement
        #replacement_values = ''.join(choice(ascii_lowercase) for i in range(10))
        # For now... replacing with the iteration count
        replacement_values = str(iteration)

        # Replace the placeholders
        resource_string = resource_string % (replacement_values)

        # Convert the string back to json and return it
        return json.loads(resource_string)

    else:

        print("No occurences of decimal placeholder found in JSON, therefore nothing will be replaced")
        return resource_structure


def multiply(resource_name, resource_structure, count):
    """Multiply resources and create copies of them.

    Parameters
    ----------
    resource_name : string
        The resource name.
    resource_structure : JSON
        CloudFormation resource definition.
    count : Integer
        Amount of copies thar are goint to be created.

    Returns
    -------
    type
        Dictonary with the replicated resources.

    """
    resources = {}
    # Loop according to the number of times we want to
    # multiply, creating a new resource each time
    for iteration in range(1, (count + 1)):
        print("Multiplying '{}', iteration count {}".format(resource_name,iteration))
        multipliedResourceStructure = update_placeholder(resource_structure,iteration)
        resources[resource_name+str(iteration)] = multipliedResourceStructure
    return resources


def handler(event, context):
    result = process_template(event['fragment'],event['templateParameterValues'])
    return {
        'requestId': event['requestId'],
        'status': result[0],
        'fragment': result[1],
    }
