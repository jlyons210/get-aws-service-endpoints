# get-aws-service-endpoints
Polls the AWS SSM API to retrieve endpoints for all or specified regions and services.

Messages are printed to `stderr`, and the JSON to `stdout` so that JSON output can be piped/redirected.

## Examples

### All endpoints

```
$ ./get-aws-service-endpoints.py > all-endpoints.json
This script will retrieve all AWS service endpoints for all services in all regions.
This will make a large number of API calls and may take a long time.
Are you sure you want to continue? (y/n) y
Retrieving all AWS regions... found 32 regions.
Retrieving all services in af-south-1... found 182 services.
Retrieving endpoints for af-south-1...................... done.
...
$ cat all-endpoints.json
{
    "af-south-1": {
        "accessanalyzer": "access-analyzer.af-south-1.amazonaws.com",
        "account": "account.us-east-1.amazonaws.com",
        "acm-pca": "acm-pca.af-south-1.amazonaws.com",
        "acm": "acm.af-south-1.amazonaws.com",
...
```

### S3 endpoints in us-east-1, us-east-2, and eu-west-1

```
$ ./get-aws-service-endpoints.py --services s3 --regions us-east-1,us-east-2,eu-west-1
Retrieving endpoint(s) for s3 in eu-west-1.... done.
Retrieving endpoint(s) for s3 in us-east-1.... done.
Retrieving endpoint(s) for s3 in us-east-2.... done.
{
    "eu-west-1": {
        "s3": "s3.eu-west-1.amazonaws.com"
    },
    "us-east-1": {
        "s3": "s3.us-east-1.amazonaws.com"
    },
    "us-east-2": {
        "s3": "s3.us-east-2.amazonaws.com"
    }
}
```