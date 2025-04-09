import boto3
from google.cloud import compute_v1
from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
import logging

def run(target, profile):
    results = {}
    creds = profile["credentials"]
    
    if "aws" in profile["cloud_providers"]:
        try:
            ec2 = boto3.client("ec2", aws_access_key_id=creds["aws"]["access_key"],
                            aws_secret_access_key=creds["aws"]["secret_key"])
            instances = ec2.describe_instances()
            results["aws"] = {"instances": len(instances["Reservations"])}
        except Exception as e:
            logging.error(f"AWS recon failed: {e}")
            results["aws"] = {"error": str(e)}

    if "gcp" in profile["cloud_providers"]:
        try:
            client = compute_v1.InstancesClient()
            instances = client.aggregated_list(project=creds["gcp"]["project_id"])
            results["gcp"] = {"instances": sum(1 for _ in instances)}
        except Exception as e:
            logging.error(f"GCP recon failed: {e}")
            results["gcp"] = {"error": str(e)}

    if "azure" in profile["cloud_providers"]:
        try:
            credential = DefaultAzureCredential()
            client = ComputeManagementClient(credential, creds["azure"]["subscription_id"])
            vms = client.virtual_machines.list_all()
            results["azure"] = {"vms": sum(1 for _ in vms)}
        except Exception as e:
            logging.error(f"Azure recon failed: {e}")
            results["azure"] = {"error": str(e)}

    return results
