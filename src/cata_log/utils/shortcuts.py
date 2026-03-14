from cata_log import constants, database


def get_config(config_name: str) -> str:
    """Get a config value from database or the defaults.

    Args:
        config_name: The name of the configuration.

    Returns:
        The config value.

    Raises:
        AttributeError: If there is no config with that name.
    """
    with database.DBSession() as db_session:
        config = (
            db_session.query(database.Config)
            .filter(database.Config.name == config_name)
            .one_or_none()
        )
        return config.value if config else getattr(constants.DefaultConfig, config_name)
