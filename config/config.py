import constants


def config(env=constants.DEFAULT_ENV):
    """
    return to the corresponding configuration according to different environments
    :param env: Current environment variable
    :return: conf_dict
    """
    if env == 'prod':
        import config.config_prod as conf
    elif env == 'uat':
        import config.config_uat as conf
    else:
        import config.config_dev as conf

    config_map = {
        'host': conf.host,
        'port': conf.port,
        'sid': conf.sid,
        'username': conf.username,
        'password': conf.password,
        'redis_host': conf.redis_host,
        'redis_port': conf.redis_port,
        'WIN_SERVER': conf.WIN_SERVER,
        'PDF_TO_HTML_URL': conf.PDF_TO_HTML_URL,
        'log_path': conf.log_path
    }

    return config_map
