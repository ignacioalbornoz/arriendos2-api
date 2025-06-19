from pydantic import PositiveInt
from sqlalchemy import delete
from sqlalchemy.future import select
from shared_models.base import get_class_by_entity_name
from shared_models.user_restaurants.user_table_sessions import UserTableSession
from shared_models.user_restaurants.user_session_runners import UserTableSessionRunner
from shared_models.orders.order_details import OrderDetail
from shared_models.orders.consumable_order_detail import ConsumableOrderDetail
from repository.session import SessionDAL
from repository.orders.orders import delete_order
from repository.user_restaurants.user_table_sessions import (
    add_entity_to_user_table_session,
    get_active_user_table_session_by_table_id,
)
from repository.runners import get_active_runners_by_restaurant, get_runner_by_id
from repository.user_restaurants.user_session_runners import (
    get_user_table_session_runner_by_user_table_session_id,
)
from dependencies.base import get_model_instance_by_id
import repository.orders.consumable_histories as consumable_histories
import random


# Elimina una entidad asociada a una Transaction que salió mal.
def delete_transaction_entity(entity_name, entity_id, session: SessionDAL, commit=True):
    if entity_name == "order":
        delete_order(entity_id, session, commit=commit)
    else:
        Entity = get_class_by_entity_name(entity_name)
        session.delete_from_query(
            delete(Entity).where(Entity.id == entity_id), commit=commit
        )


# Obtiene una entidad a partir de su nombre y su id.
def get_transaction_entity(entity_name, entity_id, session: SessionDAL):
    Entity = get_class_by_entity_name(entity_name)
    return get_model_instance_by_id(Entity, entity_id, session)


# Agrega una entidad a una UserTableSession si la transacción asociada a la entidad salió bien.
# Actualiza la entidad a pagado
def approve_transaction_entity(
    entity_name,
    entity_instance,
    user_table_session_id,
    session: SessionDAL,
    commit=True,
):
    session.update(entity_instance, {"payment_status": "pagado"}, commit=False)
    entity_table_session = add_entity_to_user_table_session(
        entity_name,
        entity_instance.id,
        user_table_session_id,
        session,
        commit=False,
        flush=False,
    )
    if commit:
        session.commit()
    return entity_table_session


# Elimina la entidad de la UserTableSession.
def delete_entity_from_user_table_session(
    entity_instance, entity_table_session, session: SessionDAL, commit=True
):
    session.update(entity_instance, {"payment_status": "no pagado"}, commit=False)
    session.delete(entity_table_session, hard=True, commit=commit)


# Obtiene una UserTableSession a partir de su id, si está desactivado escoge el próximo runner.
def get_user_table_session_by_entity(
    entity_name, user_table_session_id: PositiveInt, session: SessionDAL
):
    user_table_session_instance = get_model_instance_by_id(
        UserTableSession, user_table_session_id, session
    )
    if not user_table_session_instance.active and entity_name == "order":
        # Verifica si habia un runner asociado a la mesa, en caso contrario agrega uno al azar
        active_table_session = get_active_user_table_session_by_table_id(
            user_table_session_instance.table_id,
            user_table_session_instance.id,
            session,
        )
        if active_table_session:
            user_table_session_runner_instance = (
                get_user_table_session_runner_by_user_table_session_id(
                    active_table_session.id, session
                )
            )
            runner_instance = get_runner_by_id(
                user_table_session_runner_instance.runner_user_id, session
            )
        else:
            runner_instance = get_runner_instace_for_table_session(
                user_table_session_instance, session
            )

        return user_table_session_instance, runner_instance
    return None, None


# Función que determina como se eligen runners para la sesion de la mesa
def get_runner_instace_for_table_session(user_table_session_instance, session):
    runner_instances = get_active_runners_by_restaurant(
        user_table_session_instance.restaurant_id, session
    )
    runner_instance = random.choice(runner_instances) if runner_instances else None

    return runner_instance


# Obtiene un el próximo runner disponible para una mesa (o nulo si ya tiene uno asignado).
def get_next_runner_for_table(
    user_table_session_instance: UserTableSession, session: SessionDAL
):
    if not user_table_session_instance.active:
        active_table_session = get_active_user_table_session_by_table_id(
            user_table_session_instance.table_id,
            user_table_session_instance.id,
            session,
        )
        if active_table_session:
            user_table_session_runner_instance = (
                get_user_table_session_runner_by_user_table_session_id(
                    active_table_session.id, session
                )
            )
            runner_instance = get_runner_by_id(
                user_table_session_runner_instance.runner_user_id, session
            )
        else:
            runner_instance = get_runner_instace_for_table_session(
                user_table_session_instance, session
            )
        return runner_instance
    return None


# Recibe UserTableSession, lo activa y le asigna el runner entregado.
def activate_user_table_session(
    user_table_session_instance,
    runner_instance,
    session: SessionDAL,
    commit=True,
    flush=False,
):
    session.update(user_table_session_instance, {"active": True}, commit=commit)
    return session.create(
        UserTableSessionRunner,
        {
            "user_table_session_id": user_table_session_instance.id,
            "runner_user_id": runner_instance.user_id,
        },
        commit=commit,
        flush=flush,
    )


# Recibe UserTableSession y lo activa.
def activate_user_table_session_by_runner(
    user_table_session_instance, session: SessionDAL, commit=True, flush=False
):
    session.update(user_table_session_instance, {"active": True}, commit=commit)
    return session.create(
        UserTableSessionRunner,
        {
            "user_table_session_id": user_table_session_instance.id,
            "runner_user_id": session.user.id,
        },
        commit=commit,
        flush=flush,
    )


# Desactiva UserTableSession y elimina el runner asociado.
def deactive_user_table_session(
    user_table_session_instance,
    runner_table_session_instance,
    session: SessionDAL,
    commit=True,
):
    session.update(user_table_session_instance, {"active": False}, commit=commit)
    session.delete(
        runner_table_session_instance,
        hard=True,
        commit=commit,
    )


# Obtiene todos los detalles de una orden a partir de su id.
def get_consumables_by_order_id(order_id: PositiveInt, session: SessionDAL):
    select_query = (
        select(ConsumableOrderDetail)
        .join(OrderDetail, OrderDetail.id == ConsumableOrderDetail.order_detail_id)
        .where(OrderDetail.order_id == order_id)
    )
    consumable_history_instances = session.get_all(select_query, 0, 100)
    return consumable_history_instances


# Actualiza el estado de los consumibles a "en fila".
def update_consumables_to_en_fila(
    consumable_history_instances, session: SessionDAL, commit=True, flush=False
):
    new_status = "en fila"
    consumable_histories.update_consumable_histories(
        consumable_history_instances, new_status, session, commit=commit, flush=flush
    )


# Anula los consumibles de una orden.
def cancel_consumables_by_order_id(
    consumable_history_instances, session: SessionDAL, commit=True, flush=False
):
    new_status = "anulado"
    consumable_histories.update_consumable_histories(
        consumable_history_instances, new_status, session, commit=commit, flush=flush
    )


# # Pone en estado pagado y asocia una Entity a una UserTableSession si la Transaction asociada a la entidad salió bien.
# def approve_transaction_and_update_order(
#     entity_name: str,
#     entity_id: PositiveInt,
#     user_table_session_id: PositiveInt,
#     session: SessionDAL,
#     commit=True,
# ):
#     Entity = get_class_by_entity_name(entity_name)
#     if Entity:
#         add_entity_to_user_table_session(
#             entity_name, entity_id, user_table_session_id, session, commit=False
#         )
#         user_table_session_instance = get_model_instance_by_id(
#             UserTableSession, user_table_session_id, session
#         )

#         # Primera compra activa la sesión
#         if not user_table_session_instance.active and entity_name == "order":
#             session.update(user_table_session_instance, {"active": True})

#             # Verifica si habia un runner asociado a la mesa, en caso contrario agrega uno al azar
#             active_table_session = get_active_user_table_session_by_table_id(
#                 user_table_session_instance.table_id,
#                 user_table_session_instance.id,
#                 session,
#             )
#             if active_table_session:
#                 user_table_session_runner_instance = (
#                     get_user_table_session_runner_by_user_table_session_id(
#                         active_table_session.id, session
#                     )
#                 )
#                 runner_instance = get_runner_by_id(
#                     user_table_session_runner_instance.runner_user_id, session
#                 )
#             else:
#                 runner_instances = get_active_runners_by_restaurant(
#                     user_table_session_instance.restaurant_id, session
#                 )
#                 runner_instance = (
#                     random.choice(runner_instances) if runner_instances else None
#                 )

#             # Agrega el runner
#             if runner_instance:
#                 session.create(
#                     UserTableSessionRunner,
#                     {
#                         "user_table_session_id": user_table_session_instance.id,
#                         "runner_user_id": runner_instance.user_id,
#                     },
#                     commit=False,
#                 )
#                 # Primera compra activa la sesión

#         session.update_from_query(
#             update(Entity)
#             .where(Entity.id == entity_id)
#             .values(payment_status="pagado"),
#             commit=commit,
#         )
#         if entity_name == "order":
#             # envía las ordenes a "en fila"
#             select_query = (
#                 select(ConsumableOrderDetail)
#                 .join(
#                     OrderDetail, OrderDetail.id == ConsumableOrderDetail.order_detail_id
#                 )
#                 .where(OrderDetail.order_id == entity_id)
#             )
#             consumable_history_instances = session.get_all(select_query, 0, 100)
#             new_status = "en fila"

#             consumable_histories.update_consumable_histories(
#                 consumable_history_instances, new_status, session
#             )


"""
# Elimina la entidad si es que no se pudo concretar la transacción en 5 minutos. De paso
# también elimina la transacción misma.
async def check_transaction_timeout(transaction_instance, entity_instance, session: SessionDAL):
    await asyncio.sleep(310)  # Wait for 5 minutes
    session.refresh(transaction_instance)
    if not transaction_instance.done:
        session.refresh(entity_instance)
        entity_name = type(entity_instance).get_entity_name()
        print(f"Transaction timed out for {entity_name} {entity_instance.id}")
        # delete_transaction_entity(entity_name, entity_instance.id, session, commit=False)
    
    # session.delete(transaction_instance)
"""


# Restaura la validación de la transacción y anula los consumibles asociados a la orden. Dependiendo
# del progreso indicado.
def restore_transaction_validation(
    progress: int,
    transaction_instance,
    entity_instance,
    entity_table_session,
    user_table_session_instance,
    runner_table_session_instance,
    consumable_history_instances,
    session: SessionDAL,
):
    if progress == 4:
        # Se desactiva la sesión de la mesa si es la primera compra
        deactive_user_table_session(
            user_table_session_instance, runner_table_session_instance, session
        )
    if progress >= 3:
        # Se cancelan los consumibles
        cancel_consumables_by_order_id(consumable_history_instances, session)

    if progress >= 2:
        # Se desaprueba la entidad
        delete_entity_from_user_table_session(
            entity_instance, entity_table_session, session
        )

    if progress >= 1:
        # Se marca la transacción con un status done=False.
        session.update(transaction_instance, {"done": False})
