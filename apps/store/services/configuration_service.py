
def get_store_config():

    from apps.store.models.store_configuration import (
        StoreConfiguration
    )

    config = StoreConfiguration.objects.first()

    if not config:
        raise ValueError(
            "StoreConfiguration not found"
        )

    return config