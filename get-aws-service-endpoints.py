#!/usr/bin/env python3
"""List AWS service endpoints for all (or specified) services in all (or specified) regions"""

import argparse
import json
import sys
import boto3
import botocore.exceptions

AWS_SDK_RETRIES_MAX_ATTEMPTS = 10
AWS_SDK_RETRIES_MODE = 'standard'


def confirm_unfiltered_execution() -> None:
    """
    Confirms unfiltered execution

    :return: None
    """

    print('This script will retrieve all AWS service endpoints for all services in all regions.')
    print('This will make a large number of API calls and may take a long time.')
    print('Are you sure you want to continue? (y/n) ',
          end = '',
          flush = True,
          file = sys.stderr)

    if input().lower() != 'y':
        quit_error('User aborted program')


def create_client(service_name) -> object:
    """
    Configure boto3 client

    :param service_name: AWS service name
    :return: boto3 client
    """

    return boto3.client(
        service_name = service_name,
        config = boto3.session.Config(
            retries = {
                'max_attempts': AWS_SDK_RETRIES_MAX_ATTEMPTS,
                'mode': AWS_SDK_RETRIES_MODE,
            }
        )
    )


def generate_output_json() -> str:
    """
    Generate JSON output

    :return: JSON output
    """

    ssm_client = create_client('ssm')
    regions = get_regions(ssm_client)

    region_service_endpoints = []

    for region in regions:
        region_services = get_region_services(ssm_client, region)

        if not arguments.service_overrides:
            print(f'Retrieving endpoints for {region}...',
                  end = '',
                  flush = True,
                  file = sys.stderr)
        else:
            print(f'Retrieving endpoint(s) for {", ".join(region_services)} in {region}...',
                  end = '',
                  flush = True,
                  file = sys.stderr)

        region_service_endpoints.extend(
            get_service_endpoints(ssm_client, region, region_services)
        )

        print(' done.', file = sys.stderr)

    json_data = {}

    for region, service, endpoint in region_service_endpoints:
        if region not in json_data:
            json_data[region] = {}

        json_data[region][service] = endpoint

    return json.dumps(json_data, indent = 4)


def get_regions(ssm_client) -> []:
    """
    Populates a list of AWS regions, or uses provided regions

    :param ssm_client: boto3 client
    :return: list of regions
    """

    region_overrides = \
        arguments.region_overrides.split(',') if arguments.region_overrides else None

    if region_overrides:
        regions = region_overrides

    else:
        print('Retrieving all AWS regions... ', end = '', flush = True, file = sys.stderr)

        regions = []
        paginator = ssm_client.get_paginator('get_parameters_by_path')
        iterator = paginator.paginate(
            Path = '/aws/service/global-infrastructure/regions'
        )

        regions = [region['Value']
                   for page in iterator
                   for region in page['Parameters']
                   if region['Value'] != 'global']

        print(f'found {len(regions)} regions.', file = sys.stderr)

    return sorted(regions)


def get_region_services(ssm_client, region) -> []:
    """
    Populates a list of services in a region, or uses provided services

    :param ssm_client: boto3 client
    :param region: AWS region
    :return: list of services
    """

    service_overrides = \
        arguments.service_overrides.split(',') if arguments.service_overrides else None

    if service_overrides:
        region_services = service_overrides

    else:
        print(f'Retrieving all services in {region}... ', end = '', flush = True, file = sys.stderr)

        region_services = []
        paginator = ssm_client.get_paginator('get_parameters_by_path')
        iterator = paginator.paginate(
            Path = f'/aws/service/global-infrastructure/regions/{region}/services'
        )

        region_services = [service['Value']
                           for page in iterator
                           for service in page['Parameters']]

        print(f'found {len(region_services)} services.', file = sys.stderr)

    return sorted(region_services)


def get_service_endpoints(ssm_client, region, services) -> []:
    """
    Populates a list of service endpoints in a region

    :param ssm_client: boto3 client
    :param region: AWS region
    :param services: list of AWS services
    :return: list of service endpoints
    """

    parameter_names = []

    for service in services:
        parameter_names.append(
            f'/aws/service/global-infrastructure/regions/{region}/services/{service}/endpoint'
        )

    # SSM GetParameters API supports a maximum of 10 parameters per call
    service_endpoints = []

    for i in range(0, len(parameter_names), 10):
        batch_response = ssm_client.get_parameters(
            Names = parameter_names[i:i + 10]
        )

        print('.', end = '', flush = True, file = sys.stderr)

        for parameter in batch_response['Parameters']:
            service = parameter['Name'].split('/')[-2]
            service_endpoints.append([ region, service, parameter['Value'] ])

    return service_endpoints


def parse_arguments() -> argparse.Namespace:
    """
    Populates chosen source and target regions from command line arguments.

    Returns:
    Source and target region arguments (Namespace)
    """

    parser = argparse.ArgumentParser(
        description = 'This script will retrieve all AWS service endpoints for all (or ' \
                      'specified) services in all (or specified) regions.',
        formatter_class = argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument('--regions', '-r',
                        dest='region_overrides',
                        help='Overrides with specified regions, comma-separated',
                        required = False)

    parser.add_argument('--services', '-s',
                        dest='service_overrides',
                        help='Overrides with specified services, comma-separated',
                        required = False)

    parser.add_argument('--version', '-v',
                        action = 'version',
                        version = '1.0.0',
                        help = 'Prints version information')

    return parser.parse_args()


def quit_error(message) -> None:
    """
    Exit with an error message

    :param message: error message
    :return: None
    """

    print(message, file = sys.stderr)
    exit(1)


def main() -> None:
    """
    Main function

    :return: None
    """

    # Are you sure you want to make thousands of API calls?
    if not arguments.region_overrides and not arguments.service_overrides:
        confirm_unfiltered_execution()

    # Do the needful
    output_json = generate_output_json()
    print(output_json)


if __name__ == '__main__':
    try:
        arguments = parse_arguments()
        main()

    except botocore.exceptions.NoCredentialsError as e:
        quit_error(e)

    except botocore.exceptions.ClientError as e:
        quit_error(e.response['Error']['Message'])

    except KeyboardInterrupt:
        quit_error('User interrupted program')
