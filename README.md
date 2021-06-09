# AWS Dev Fabric for SQL Server

Microsoft made changes to the MSDN license terms that prohibit BYOL of MSDN subscriptions effective after 10/2019. The good news is that SQL Server Developer Edition is now a free download independent of MSDN, which can be deployed on shared and dedicated tenant AWS environments. While many customers may use MSDN to cover Windows Server licensing on premises, they must have a Windows Server License to run the database on AWS due to the inability to bring MSDN licenses.

At AWS, we offer customers the option to run SQL Server Developer Edition on Amazon EC2 instances based on Linux OS, which helps customers move away from MSDN for Windows Server licenses. However, this still requires DBAs to have the necessary skills to operate a Linux OS. The AWS Dev Fabric for SQL Server allows customers to keep their SQL Server within a development environment running on AWS, while removing the need for customers to subscribe to MSDN and license Windows Server on Amazon EC2 to run SQL Server Developer Edition.

The AWS Dev Fabric for SQL Server orchestrates AWS services like Fargate, ECS, CloudMap, CloudWatch, EFS, Lambda, and AWS Backup, offering a serverless solution for running SQL Server Developer edition into containers, at the same time, automatically taking care of data persistence, monitoring, log management, backup and auto-recovery.

- [What does the solution offer?](#what-does-the-solution-offer-?)
- [How to deploy the solution](#how-to-deploy-the-solution)
  - [Control plane](#control-plane)
  - [Data plane](#data-plane)
- [Architecture](#architecture)
- [Project structure and template anatomy](#project-structure-and-template-anatomy)
- [Considerations](#considerations)
- [Contributing to the project](#contributing-to-the-project)
- [Changelog](#changelog)
- [License](#license)

#### Security disclosures

If you think you’ve found a potential security issue, please do not post it in the Issues.  Instead, please follow the instructions [here](https://aws.amazon.com/security/vulnerability-reporting/) or email AWS security directly at [aws-security@amazon.com](mailto:aws-security@amazon.com).

## What does the solution offer?

It allows you to deploy and create [ECS Fargate containers](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/AWS_Fargate.html) using [Microsoft SQL Server Images](https://hub.docker.com/_/microsoft-mssql-server). This will easily and seamlessly provision serverless Microsoft SQL instances for development environments. You can fine control the Network settings (VPC and subnets), SQL Instance configuration (RAM, CPU Cores, etc) and the specific Image version you would like to use.

You can launch any number of SQL Instances you require in minutes. Each Database will have its own unique endpoint, password and storage allocation.

In order to leverage security, the Security Groups are configured to only allow the minimum required traffic. Also, the deployment explicitly validates that the selected subnets are [private](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Scenario2.html). As a best practice, Database servers should not be accessible publicly over the internet. In any case, please always double check and ensure that private subnets are selected.

As the solution is designed for development workloads, it leverages options for minimising costs:
- You can opt-in for running the SQL Instances in [Fargate Spot](https://aws.amazon.com/blogs/aws/aws-fargate-spot-now-generally-available/). This can significantly reduce the operational costs.
- You can define a weekly schedule for starting and stopping your SQL Server Instances during office hours.

As the engine configuration and the data are [securely stored in EFS](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/efs-volumes.html), containers can be started, stopped and replaced (in case of malfunction) without affecting or losing data.

Finally, each SQL Instance will be accompanied by a simple web-server file manager (running as a side-car container within the same ECS Task) for easily uploading and downloading database files and configurations. This allows you to quickly test datasets and load database backups.

## How to deploy the solution

The solution deployment is fully automated in [CloudFormation](https://aws.amazon.com/cloudformation/). Before deploying, you will need to **pack** the templates, a process that will [upload local artifacts to an S3 bucket](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-cli-package.html). This will consolidate the project templates for seamlessly deploying the solution.

Regarding the parameters, you will find self explanatory comments and parameter names while deploying the solution through the AWS Web Console.

### Step by step

1. Locate an S3 bucket, where CloudFormation templates will be stored. This Bucket **must** be in the same region were you will deploy the solution. If using Linux or MacOS, you can export the variables for smooth usage:

```
export the_region=<your-aws-region>
export the_bucket=<your-selected-s3-bucket>
```

2. Clone the repository

```
git clone https://github.com/aws-samples/aws-dev-fabric-for-sql-server.git
```

... or [download](https://github.com/aws-samples/aws-dev-fabric-for-sql-server/archive/master.zip) it directly as a zip.

3. Step into the repository folder

```
cd aws-dev-fabric-for-sql-server
```

#### Control plane

- **Package ...**
```
aws --region=$the_region cloudformation package --template-file ./control-plane/control-plane.yaml --s3-bucket $the_bucket --output-template-file ./packaged-control-plane.yaml
```

- **Deploy ...**

You can use the [AWS Web console to deploy](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cfn-console-create-stack.html)! Upload the **packaged-control-plane.yaml** file. Alternatively, you can deploy via CLI as well:
```
aws --region=$the_region cloudformation create-stack \
       --template-body file://packaged-control-plane.yaml \
       --stack-name <the-stack-name> \
       --disable-rollback \
       --capabilities CAPABILITY_AUTO_EXPAND CAPABILITY_NAMED_IAM \
       --parameters \
       ParameterKey=TheVPCID,ParameterValue="<the-vpc>" \
       ParameterKey=SubnetPrivateAZ1,ParameterValue="<subnet-prviate-1>" \
       ParameterKey=SubnetPrivateAZ2,ParameterValue="<subnet-prviate-2>"
```

#### Data plane

- Package ...
```
aws --region=$the_region cloudformation package --template-file ./data-plane/data-plane.yaml --s3-bucket $the_bucket --output-template-file packaged-data-plane.yaml
```

- Deploy ...

You can use the [AWS Web console to deploy](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cfn-console-create-stack.html)! Upload the **packaged-data-plane.yaml** file. Alternatively, you can deploy via CLI as well:

```
aws --region=$the_region cloudformation create-stack \
       --template-body file://packaged-data-plane.yaml \
       --stack-name <the-stack-name> \
       --disable-rollback \
       --capabilities CAPABILITY_AUTO_EXPAND CAPABILITY_NAMED_IAM
```


## Architecture

The SQL Server Dev Fabric allows you to create a fleet of SQL Server 2017/2019 Developer Edition running on **Ubuntu 16.04/18.04** on top of Amazon Elastic Container Service (ECS Fargate). The solution helps customers reduce all the heavy-lift imposed by using EC2 or/and ECS + EC2 Deployment (OS Patching, Management, Hardening, Snapshots and AMI Lifecycle), allowing customers to quickly scale up to thousands SQL Server Instances in minutes, with SQL Server Auto-Recovery and Data Persistence. The solution splits into two modules.

#### Control plane

Ideally, you would have one **Control Plane** deployed per AWS region. This setup takes care of creating and provisioning all the common and underlying resources for the solution to work:

- Checks and validates that input subnets are private.
- Creates the [ECS Cluster](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/clusters.html).
- Creates the [EFS shared filesystem](https://aws.amazon.com/efs/) and the [backup policies](https://docs.aws.amazon.com/efs/latest/ug/efs-backup-solutions.html).
- Provisions other CloudFormation resources required for the solution setup, such as [Custom Resources](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/template-custom-resources.html) and [Macros](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/template-macros.html).

![control plane](docs/ControlPlane.png)

#### Data plane

You can deploy as many data planes as you require. This deployment allows you to provision **N** unique databases. Each of them will have a dedicated set of resources, unique and isolated:

- A Docker container for running the database engine.
- A portion/directory within the EFS volume for storing the data.
- A dedicated web access for retrieving and adding files to the engine.
- Its own set of unique and randomly generated passwords.
- Its own IAM roles and permissions.

This is useful for creating multiple and isolated environments with similar setups, in minutes.

You can later deploy new and different instances of the Data Plane, specifying different engine versions, capabilities, permissions, etc.

![data plane](docs/DataPlane.png)

## Project structure and template anatomy

The project structure uses [nested Stacks](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-nested-stacks.html) for deploying the resources in a structured and tidy manner. The CloudFormation templates are subdivided into [Control plane](#control-plane) and [Data plane](#data-plane) directories, which are [deployed separately](#how-to-deploy-the-solution).

In the **control-plane** section, you will find the CloudFormation definitions for common resources and custom resources that create the base infrastructure for the solution. You will generally not require to check or explore these files. Typically you will deploy this template once per region.

In the **data-plane** section, you will find the *data-plane.yaml* template. You will deploy this template each time you would like to create a new set of *N* Database engine instances. This template will be pre-processed by the [sqlserverdevfabric-macro macro](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/template-macros.html) and will finally use the *fargate-sql-service.yaml* templae for deploying all the required resources for the Database Engine (ECS Service, Task Definition, Secrets, EFS Endpoints, etc). Note that each of these deployments are unique and will be part of a single isolated Stack.

As a sample use case, suppose there is a new project where an internal team requested 5 different SQL Databases for testing and developing features in parallel. You can deploy a new **data-plane** Stack, selecting to deploy 5 Instances. This will create a new set of 5 SQL Instances with its own unique credentials and DNS endpoints. You can distribute the access details to the team members, being able to create such environments in minutes. Each of the created SQL Instances will have a similar configurations (RAM, CPU allocation, etc) but they will have unique credentials and endpoints.

The parameters are generally self-explanatory and you will also find a handy description in the AWS Web Console while deploying the templates. The most important ones are:

**control-plane.yaml**
 - *ECS Cluster name* -> Defines the name for the main ECS Cluster that will hold all the database engines. This cluster will be created as part of the solution.
 - *Root DNS name* -> Domain name you would like to use for the solution. This will be used as the suffix for each of the created SQL Instances. Each of the SQL Instances will be accessed via *<unique-id>.sqlserverdev.fabric*.
 - *Networking settings* -> Defines the VPC and Subnets where the SQL instances will be placed. The subnets must be private.

**data-plane.yaml**
- *ECS Cluster name* -> ECS Cluster for deploying the set of instances. This cluster must match the name defined in the **control-plane** section.
- *SQL Instance count* -> How many SQL Instances you would like to deploy.
- *SQL Server configuration* -> Specific configurations for the SQL Instances (vCPUs, RAM, SQL Docker Image and version, etc). All the instances will have similar configurations.

The project structure looks as follows:

```
.
├── control-plane
│   ├── control-plane.yaml
│   ├── custom-resources
│   │   ├── custom-resources.yaml
│   │   ├── src_custom_resources
│   │   │   └── ** .py files for the custom resources code **
│   │   └── src_macro
│   │       ├── __init__.py
│   │       └── index.py
│   └── storage-manager
│       └── storage-manager.yaml
└── data-plane
    ├── data-plane.yaml
    └── fargate-sql-service
        └── fargate-sql-service.yaml
```


## Considerations

We encourage everyone to report issues and feature requests in [this section](https://github.com/aws-samples/aws-dev-fabric-for-sql-server/issues). This will help to improve the solution and expand it to different use cases.

- Currently, it is not possible to add customisations or settings to the SQL engine. Selecting the **SQL Server collation** is the only available option for now. This will be hopefully expanded in subsequent releases.
- As the data is stored in EFS, the solution offers reasonable performance for development environments but it will not be suitable for production workloads.
- The solution is currently available for ECS only. EKS clusters are not supported.
- Even though the solution is fully automated, the concept and pattern for running such workloads on Linux containers is relatively new. This may be something to consider if you do not have basic expertise with containers.


## Contributing to the project

Contributions and feedback are welcome! Proposals and pull requests will be considered and responded. For more information, see the [CONTRIBUTING](https://github.com/aws-samples/aws-dev-fabric-for-sql-server/blob/master/CONTRIBUTING.md) file.

Amazon Web Services does not currently provide support for modified copies of this software.


## Changelog

Refer to the [Changelog section](./CHANGELOG.md).


## License

The AWS Dev fabric for SQL Server solution is distributed under the [MIT-0 License](https://github.com/aws/mit-0). See [LICENSE](https://github.com/aws-samples/aws-dev-fabric-for-sql-server/blob/master/LICENSE) for more information.
