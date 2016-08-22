import base64
import logging
import os
import tempfile
import zipfile

from core.tasks import BaseTask
from salesforce_api.metadata import ApiDeploy
from salesforce_api.metadata import ApiRetrieveInstalledPackages
from salesforce_api.metadata import ApiRetrievePackaged
from salesforce_api.metadata import ApiRetrieveUnpackaged

class BaseSalesforceTask(BaseTask):
    name = 'BaseSalesforceTask'

    def __init__(self, project_config, task_config, org_config, **kwargs):
        self.org_config = org_config
        self.options = kwargs
        super(BaseSalesforceTask, self).__init__(project_config, task_config)

    def __call__(self):
        self._refresh_oauth_token()
        return self._run_task()

    def _run_task(self):
        raise NotImplementedError('Subclasses should provide their own implementation')

    def _refresh_oauth_token(self):
        self.org_config.refresh_oauth_token(self.project_config.keychain.app)

class BaseSalesforceMetadataApiTask(BaseSalesforceTask):
    api_class = None
    name = 'BaseSalesforceMetadataApiTask'

    def _get_api(self):
        return self.api_class(self)
   
    def _run_task(self):
        api = self._get_api()
        if self.options:
            return api(**options)
        else:
            return api()

class GetInstalledPackages(BaseSalesforceMetadataApiTask):
    api_class = ApiRetrieveInstalledPackages
    name = 'GetInstalledPackages'

class RetrieveUnpackaged(BaseSalesforceMetadataApiTask):
    api_class = ApiRetrieveUnpackaged

class RetrievePackaged(BaseSalesforceMetadataApiTask):
    api_class = ApiRetrievePackaged

class Deploy(BaseSalesforceMetadataApiTask):
    api_class = ApiDeploy
    task_options = {
        'path': {
            'description': 'The path to the metadata source to be deployed',
            'required': True,
        }
    }

    def _get_api(self):
        path = self.task_config['options']['path']

        # Build the zip file
        zip_file = tempfile.TemporaryFile()
        zipf = zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED)
        
        os.chdir(path)
        for root, dirs, files in os.walk('.'):
            for f in files:
                zip_path = os.path.join(root, f)
                zipf.write(os.path.join(root, f))
        zipf.close()
        zip_file.seek(0)
        package_zip = base64.b64encode(zip_file.read())

        return self.api_class(self, package_zip)
        

    
