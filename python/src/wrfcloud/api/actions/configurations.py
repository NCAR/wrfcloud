from wrfcloud.api.actions import Action
from wrfcloud.config import get_config_from_system
from wrfcloud.config import get_all_configs_in_system


class ListModelConfigurations(Action):
    """
    Get a list of all the model configurations in the system
    """
    def validate_request(self) -> bool:
        """
        Validate the request object
        :return: True if the request is valid, otherwise False
        """
        # no required parameters
        required = []

        # optional parameters
        optional = ['configuration_name']

        # validate the request
        return self.check_request_fields(required, optional)

    def perform_action(self) -> bool:
        """
        Put a list of all model configurations in the response object
        :return: True if the action ran successfully
        """
        try:
            # get the configuration(s) from the system
            configs = get_all_configs_in_system() if 'configuration_name' not in self.request \
                else [get_config_from_system(self.request['configuration_name'])]

            # check for the configuration name not found case
            if 'configuration_name' in self.request and None in configs:
                self.errors.append(f'Configuration name not found.')
                self.log.error('Configuration name not found: ' + self.request['configuration_name'])
                return False

            # put the sanitized user data into the response
            self.response['model_configs'] = [config.sanitized_data for config in configs]
        except Exception as e:
            self.log.error('Failed to get a list of model configurations in the system', e)
            self.errors.append('General error')
            return False

        return True
