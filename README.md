# Creating an Azure Service Principal

See [this](https://github.com/Azure-Samples/resource-manager-python-resources-and-groups). I used the [portal](https://docs.microsoft.com/azure/active-directory/develop/howto-create-service-principal-portal?WT.mc_id=aiml-0000-sejuare) to create the values in the `keys.py` file.

# Fill in a `keys.py` File
This is in the `.gitignore` so you will need to create one:

```python
import os

AZURE_TENANT_ID='<TENANT_ID>'
AZURE_CLIENT_ID='<CLIENT_ID>'
AZURE_CLIENT_SECRET='<CLIENT_SECRET>'
# Get this from the actual target subscription
AZURE_SUBSCRIPTION_ID='<SUB_ID>'
```

# Run `create.py` script
If you use `python create.py --delete` it will destroy the whole
resouce group. We don't want to do that if there's additional storage accounts we attach to the MLWorkspace (like the coco dataset for example).