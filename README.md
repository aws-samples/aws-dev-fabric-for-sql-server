## Brief and usage documentation

### How to deploy

- Locate an S3 bucket, where CloudFormation templates will be stored. This Bucket must be in the same region were you will deploy the stack. Export the variables for smooth usage:

```
export the_region=<your-aws-region>
export the_bucket=<your-selected-s3-bucket>
```

- Clone the repository

```
git clone https://github.com/aws-samples/aws-dev-fabric-for-sql-server.git
```

- Step into the repository folder

```
cd aws-dev-fabric-for-sql-server
```

##### Control plane

- Package ...
```
aws --region=$the_region cloudformation package --template-file ./control-plane/control-plane.yaml --s3-bucket $the_bucket --output-template-file ./packaged-control-plane.yaml
```

- Deploy ...

You can use the AWS Web console to deploy! Upload the **packaged-control-plane.yaml** file. Alternatively, you can deploy via CLI as well:
```
aws --region=$the_region cloudformation create-stack \
       --template-body file://packaged-control-plane.yaml \
       --stack-name <the-stack-name> \
       --disable-rollback \
       --capabilities CAPABILITY_AUTO_EXPAND CAPABILITY_NAMED_IAM \
       --parameters \
       ParameterKey=ClusterName,ParameterValue="<cluster-name>" \
       ParameterKey=TheVPCID,ParameterValue="<the-vpc>" \
       ParameterKey=SubnetPrivateAZ1,ParameterValue="<subnet-prviate-1>" \
       ParameterKey=SubnetPrivateAZ2,ParameterValue="<subnet-prviate-2>"
```

##### Data plane

- Package ...
```
aws --region=$the_region cloudformation package --template-file ./data-plane/data-plane.yaml --s3-bucket $the_bucket --output-template-file packaged-data-plane.yaml
```

- Deploy ...

You can use the AWS Web console to deploy! Upload the **packaged-data-plane.yaml** file.Alternatively, you can deploy via CLI as well:

```
aws --region=$the_region cloudformation create-stack \
       --template-body file://packaged-data-plane.yaml \
       --stack-name <the-stack-name> \
       --disable-rollback \
       --capabilities CAPABILITY_AUTO_EXPAND CAPABILITY_NAMED_IAM \
       --parameters \
       ParameterKey=ClusterName,ParameterValue="<cluster-name>"
```

##### License
This library is licensed under the MIT-0 License. See the LICENSE file.
