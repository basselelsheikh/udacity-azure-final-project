#!/bin/bash

# Variables
resourceGroup="cloud-demo"
clusterName="udacity-cluster"
allowedVmSize="Standard_D4s_v3"

# Create AKS cluster
echo "Step 1 - Creating AKS cluster $clusterName"
# Use either one of the "az aks create" commands below
# For users working in their personal Azure account
# This commmand will not work for the Cloud Lab users, because you are not allowed to create Log Analytics workspace for monitoring
# az aks create \
# --resource-group $resourceGroup \
# --name $clusterName \
# --node-count 1 \
# --enable-addons monitoring \
# --generate-ssh-keys

# For Cloud Lab users
# az aks create \
# --resource-group $resourceGroup \
# --name $clusterName \
# --node-count 1 \
# --generate-ssh-keys

az aks create \
--resource-group $resourceGroup \
--name $clusterName \
--node-count 1 \
--node-vm-size $allowedVmSize \
--generate-ssh-keys

# For Cloud Lab users
# This command will is a substitute for "--enable-addons monitoring" option in the "az aks create"
# Use the log analytics workspace - Resource ID
# For Cloud Lab users, go to the existing Log Analytics workspace --> Properties --> Resource ID. Copy it and use in the command below.
az aks enable-addons -a monitoring -n $clusterName -g $resourceGroup --workspace-resource-id "/subscriptions/dd5cdf51-de40-463c-b842-e077e98bede1/resourceGroups/cloud-demo/providers/Microsoft.OperationalInsights/workspaces/loganalytics-291938"

echo "AKS cluster created: $clusterName"

# Connect to AKS cluster

echo "Step 2 - Getting AKS credentials"

az aks get-credentials \
--resource-group $resourceGroup \
--name $clusterName \
--overwrite-existing \
--verbose

echo "Verifying connection to $clusterName"

kubectl get nodes

# echo "Deploying to AKS cluster"
# The command below will deploy a standard application to your AKS cluster. 
# kubectl apply -f azure-vote.yaml