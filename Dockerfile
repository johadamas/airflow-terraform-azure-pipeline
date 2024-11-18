FROM quay.io/astronomer/astro-runtime:12.2.0

# Switch to root to install system dependencies and Terraform
USER root

# Install required system packages and Terraform
RUN apt-get update && \
    apt-get install -y --no-install-recommends wget unzip && \
    wget -q https://releases.hashicorp.com/terraform/1.9.8/terraform_1.9.8_linux_amd64.zip && \
    unzip terraform_1.9.8_linux_amd64.zip -d /usr/local/bin && \
    rm terraform_1.9.8_linux_amd64.zip && \
    apt-get remove --purge -y wget unzip && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Azure CLI
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash

# Switch back to the default 'astro' user    
USER astro
