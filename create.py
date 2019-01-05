import os
import json
import argparse
from keys import *
from datetime import datetime
from azure.mgmt.resource import ResourceManagementClient
from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.resource.resources.models import Deployment, DeploymentProperties, DeploymentMode

## Azure Machine Learning Services
import azureml
from azureml.core import Workspace, Run, Datastore, Experiment
from azureml.core.compute import ComputeTarget, AmlCompute
from azureml.core.compute_target import ComputeTargetException


def main(resource, location, workspace, compute, clear_all):
    startTime = datetime.now()
    print('#########################')
    print('Resource Group: {}\nLocation: {}\nWorkspace: {}\nCompute: {}\nReset: {}'.format(resource, location, workspace, compute, clear_all))
    print('#########################')
    
    # LOGIN
    print('logging into Azure...')
    credentials = ServicePrincipalCredentials(
        client_id=AZURE_CLIENT_ID,
        secret=AZURE_CLIENT_SECRET,
        tenant=AZURE_TENANT_ID
    )

    client = ResourceManagementClient(credentials, AZURE_SUBSCRIPTION_ID)

    # DELETE PREVIOUS RG
    if clear_all:
        print('deleting {}...'.format(resource))
        delete_async_operation = client.resource_groups.delete(resource)
        delete_async_operation.wait()
        print('done!')

    # creating RG
    print('\nCreating Resource Group')
    print('-----------------------')
    resource_group_params = {'location':location}
    print('creating "{}" at "{}"'.format(resource, location))
    print(client.resource_groups.create_or_update(resource, resource_group_params))

    # preparing ARM template for Workspace
    with open('workspace.json', 'r') as f:
        template = json.load(f)

    # find api versions
    apiVersions = {}
    for item in template['resources']:
        apiVersions[item['type']] = item['apiVersion']
    apiVersions['Microsoft.MachineLearningServices/workspaces'] = template['variables']['mlservicesVersion']
    
    # clear workspace if it exists
    # loop to delete actual workspace first
    for item in client.resources.list_by_resource_group(resource):
        if item.type == 'Microsoft.MachineLearningServices/workspaces':
            print('\ndeleting workspace {} [{}]'.format(item.name, apiVersions[item.type]))
            result = client.resources.delete_by_id(item.id, apiVersions[item.type])
            result.wait()
            break
            
    # loop to clear related workspace resources
    for item in client.resources.list_by_resource_group(resource):
        if item.tags != None and 'mlWorkspace' in item.tags and item.tags['mlWorkspace'] == workspace:
            print('\tremoving {} [{} => {}]'.format(item.name, item.type, apiVersions[item.type]))
            result = client.resources.delete_by_id(item.id, apiVersions[item.type])
            result.wait()

    # ARM Template Parameters
    parameters = {
        'workspaceName': { 'value': workspace },
        'location': { 'value': location }
    }

    print('\nCreating Workspace')
    print('-----------------------')
    result = client.deployments.create_or_update(
                resource,
                'ai_workspace_{}'.format(datetime.utcnow().strftime("-%H%M%S")),
                properties= DeploymentProperties (
                    mode=DeploymentMode.complete,
                    template=template,
                    parameters=parameters,
                )
            )
    result.wait()
    print('done!')

    print('\nCreating Workspace Compute Target')
    print('-----------------------')
    # creating compute targets
    print('Creating compute target {} in {}'.format(compute, workspace))
    subscription_id = AZURE_SUBSCRIPTION_ID
    resource_group = resource
    workspace_name = workspace

    # create workspace object
    ws = Workspace(subscription_id = subscription_id, resource_group = resource_group, workspace_name = workspace_name)

    # create compute if it doesn't already exist
    try:
        compute = ComputeTarget(workspace=ws, name=compute)
        print('Found existing compute target')
    except ComputeTargetException:
        print('Creating a new compute target...')
        compute_config = AmlCompute.provisioning_configuration(vm_size='STANDARD_NC6', min_nodes=1, max_nodes=6)
        compute = ComputeTarget.create(ws, compute, compute_config)
        compute.wait_for_completion(show_output=True)

    client.close()

    print('Done!\nTotal Time: {}'.format(datetime.now() - startTime))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Ignite Tour Resource Setup')
    parser.add_argument('-r', '--resource', help='resource group', default='AIResources', type=str)
    parser.add_argument('-l', '--location', help='resource group location', default='eastus', type=str)
    parser.add_argument('-w', '--workspace', help='workspace name', default='robots', type=str)
    parser.add_argument('-c', '--compute', help='compute', default='sauron', type=str)
    parser.add_argument('--delete', action='store_true', default=False, help='deletes entire workspace')
    args = parser.parse_args()
    main(args.resource, args.location, args.workspace, args.compute, args.delete)