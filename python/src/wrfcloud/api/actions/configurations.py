import yaml

from wrfcloud.api.actions import Action
from wrfcloud.config import WrfConfig
from wrfcloud.config import add_config_to_system
from wrfcloud.config import get_config_from_system
from wrfcloud.config import get_all_configs_in_system
from wrfcloud.config import delete_config_from_system
from wrfcloud.config import update_config_in_system


class AddModelConfiguration(Action):
    """
    Add a new model configuration to the system
    """
    def validate_request(self) -> bool:
        """
        Validate the request object
        :return: True if the request is valid, otherwise False
        """
        # expected parameters
        required = ['model_config']
        optional = []

        # validate the request
        return self.check_request_fields(required, optional)

    def perform_action(self) -> bool:
        """
        Add a new model configuration to the system
        :return: True if the action ran successfully
        """
        try:
            # build a WrfConfig object
            config: WrfConfig = WrfConfig(self.request['model_config'])

            # validate the configuration data
            if not config.validate():
                self.errors.append('Configuration is invalid.')
                self.log.error('Invalid configuration data: ' + yaml.safe_dump(config.data, indent=2))
                return False

            # check if there is already a configuration with the same name
            existing: WrfConfig = get_config_from_system(config.name)
            if existing is not None:
                self.errors.append('The configuration name is already in use. Please choose a unique name.')
                self.log.error(f'The name {config.name} is already in use.')
                return False

            # add the model configuration to the system
            ok = add_config_to_system(config)
            if ok:
                self.response['model_config'] = config.sanitized_data
            return ok
        except Exception as e:
            self.log.error('Failed to add a model configuration to the system', e)
            self.errors.append('General error')
            return False


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


class DeleteModelConfiguration(Action):
    """
    Delete a model configuration from the system
    """
    def validate_request(self) -> bool:
        """
        Validate the request object
        :return: True if the request is valid, otherwise False
        """
        # expected parameters
        required = ['configuration_name']
        optional = []

        # validate the request
        return self.check_request_fields(required, optional)

    def perform_action(self) -> bool:
        """
        Add a new model configuration to the system
        :return: True if the action ran successfully
        """
        try:
            # build a WrfConfig object
            configuration_name: str = self.request['configuration_name']

            # check if the configuration with the name already exists
            existing: WrfConfig = get_config_from_system(configuration_name)
            if existing is None:
                self.errors.append('The configuration does not exist.')
                self.log.error(f'The configuration with name, {configuration_name}, does not exist.')
                return False

            # delete the model configuration from the system
            ok = delete_config_from_system(existing)
            if ok:
                self.response['model_config'] = existing.sanitized_data
            return ok
        except Exception as e:
            self.log.error('Failed to delete a model configuration to the system', e)
            self.errors.append('General error')
            return False


class UpdateModelConfiguration(Action):
    """
    Add a new model configuration to the system
    """
    def validate_request(self) -> bool:
        """
        Validate the request object
        :return: True if the request is valid, otherwise False
        """
        # expected parameters
        required = ['model_config']
        optional = []

        # validate the request
        return self.check_request_fields(required, optional)

    def perform_action(self) -> bool:
        """
        Add a new model configuration to the system
        :return: True if the action ran successfully
        """
        try:
            # build a WrfConfig object
            config: WrfConfig = WrfConfig(self.request['model_config'])

            # validate the configuration data
            if not config.validate():
                self.errors.append('Configuration is invalid.')
                self.log.error('Invalid configuration data: ' + yaml.safe_dump(config.data, indent=2))
                return False

            # check if the configuration with the name already exists
            existing: WrfConfig = get_config_from_system(config.name)
            if existing is None:
                self.errors.append('The configuration does not exist and cannot be updated.')
                self.log.error(f'The configuration with name, {config.name}, does not exist.')
                return False

            # update the model configuration in the system
            ok = update_config_in_system(config)
            if ok:
                self.response['model_config'] = config.sanitized_data
            return ok
        except Exception as e:
            self.log.error('Failed to update a model configuration in the system', e)
            self.errors.append('General error')
            return False
