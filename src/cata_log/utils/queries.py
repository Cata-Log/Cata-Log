from sqlalchemy import ScalarSelect, sql

from cata_log import database


def latest_provider_catalog_id_subquery(provider_id: int) -> ScalarSelect[int]:
    """Create a subquery for the id of the latest catalog of a provider.

    Args:
        provider_id: The id of the provider.

    Returns:
        A subquery to use in sql queries that need the latest provider catalog id.
    """
    return (
        sql.select(database.Catalog.id)
        .filter(database.Catalog.provider_id == provider_id)
        .order_by(database.Catalog.created_at.desc())
        .limit(1)
        .scalar_subquery()
    )
