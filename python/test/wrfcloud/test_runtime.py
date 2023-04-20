"""
Test the wrfcloud.runtime module
"""


from typing import List
from wrfcloud.system import init_environment
from wrfcloud.config import WrfConfig
from helper import _get_all_sample_wrf_configurations


# initialize the test environment
init_environment(env='test')


def test_wrf_configuration() -> None:
    """
    Test the WrfConfig class
    :return: None
    """
    configs: List[WrfConfig] = _get_all_sample_wrf_configurations()

    for config in configs:
        # test getters, setters, and copy constructor
        config_ = WrfConfig(config.data)
        assert config.name == config_.name
        assert config.s3_key_wrf_namelist == config_.s3_key_wrf_namelist
        assert config.s3_key_wps_namelist == config_.s3_key_wps_namelist
        assert config.s3_key_geo_em == config_.s3_key_geo_em
        assert config.wrf_namelist == config_.wrf_namelist
        assert config.wps_namelist == config_.wps_namelist
        assert config.cores == config_.cores
        assert config.cores == 96

        # test data sanitization
        sanitized_data = config.sanitized_data
        for key in config.SANITIZE_KEYS:
            assert key not in sanitized_data
