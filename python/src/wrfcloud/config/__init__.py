"""
Other code calling the wrfcloud.config module should mainly use functions from
this file.  Calling other functions and classes may have unexpected results.
"""
__all__ = ['WrfConfig', 'ConfigDao', 'add_config_to_system', 'add_config_to_system', 'get_config_from_system',
           'get_all_configs_in_system', 'update_config_in_system', 'delete_config_from_system']

from typing import Union, List
from wrfcloud.log import Logger
from wrfcloud.config.config import WrfConfig
from wrfcloud.config.config_dao import ConfigDao


log = Logger()


def add_config_to_system(new_config: WrfConfig) -> bool:
    """
    Add a config to the system
    :param new_config: The new config to add
    :return True if added successfully
    """
    # get the DAOs
    dao = ConfigDao()

    # add the config and return status
    return dao.add_config(new_config)


def get_config_from_system(config_name: str) -> Union[WrfConfig, None]:
    """
    Get a config from the system
    :param config_name: Configuration name
    :return Configuration with matching config name, or None
    """
    # verify parameters
    if config_name is None:
        return None

    # get the config DAO
    dao = ConfigDao()

    # get config by config ID
    return dao.get_config_by_name(config_name)


def get_all_configs_in_system() -> List[WrfConfig]:
    """
    Get a list of all configs in the system
    :return: A list of all configs in the system
    """
    # create the data access object
    dao = ConfigDao()

    return dao.get_all_configs()


def update_config_in_system(update_config: WrfConfig) -> bool:
    """
    Use the DAOs to update a config in the system
    :param update_config: The complete config object with updated values (only status fields are mutable)
    :return: True if successful, otherwise False
    """
    # create objects
    dao = ConfigDao()

    # get the existing config
    existing_config = dao.get_config_by_name(update_config.name)
    if existing_config is None:
        log.error('The model configuration does not exist and cannot be updated: ' + update_config.name)
        return False

    # update config table
    update_config.name = existing_config.name  # name is immutable
    updated = dao.update_config(update_config)

    return updated


def delete_config_from_system(del_config: WrfConfig) -> bool:
    """
    Delete a config from the system
    :param del_config: config to delete from the system
    :return True if deleted, otherwise False
    """
    # get the config DAO
    dao = ConfigDao()

    # delete config
    if del_config is not None:
        return dao.delete_config(del_config)

    log.error('Value for config to remove was set as None', ValueError('del_config cannot be None'))
    return False
