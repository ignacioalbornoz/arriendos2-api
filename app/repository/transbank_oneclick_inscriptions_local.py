from repository.session import SessionDAL
import asyncio
from sqlalchemy import delete
from shared_models.base import get_class_by_entity_name


# Elimina una entidad asociada a una Inscripción que salió mal.
def delete_transaction_entity(entity_name, entity_id, session: SessionDAL, commit=True):
    Entity = get_class_by_entity_name(entity_name)
    session.delete_from_query(
        delete(Entity).where(Entity.id == entity_id), commit=commit
    )


# Elimina la OneClickInscription si es que no se pudo concretar la transacción en 5 minutos.
async def check_oneclick_inscription_timeout(
    inscription_instance, oneclickcard_instance, session: SessionDAL
):
    await asyncio.sleep(310)  # Wait for 5 minutes
    session.refresh(inscription_instance)
    if not inscription_instance.done:
        session.refresh(oneclickcard_instance)
        entity_name = type(oneclickcard_instance).get_entity_name()
        print(f"Transaction timed out for {entity_name} {oneclickcard_instance.id}")
        delete_transaction_entity(
            entity_name, oneclickcard_instance.id, session, commit=False
        )
    session.delete(inscription_instance)
