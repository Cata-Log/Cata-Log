from cata_log import constants, database


def get_config(config_name: str) -> str:
    with database.DBSession() as db_session:
        config = (
            db_session.query(database.Config)
            .filter(database.Config.name == config_name)
            .one_or_none()
        )
        return config.value if config else getattr(constants.DefaultConfig, config_name)
