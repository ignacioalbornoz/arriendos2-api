from shared_models.user_restaurants.user_oneclick import OneclickAsk
from repository.session import SessionDAL
from sqlalchemy.future import select


# Obtains the response of whether the user doesn't want to be asked about adding a one-click card
def get_oneclick_ask(session: SessionDAL) -> OneclickAsk:
    select_query = select(OneclickAsk).where(
        OneclickAsk.user_id == session.user.id,
    )
    result = session.get_all(select_query)
    return result


def create_or_update_oneclick_ask(
    user_id: int, declined: bool, session: SessionDAL
) -> OneclickAsk:
    # Fetch the existing record using session.get() or equivalent query method
    existing_record = get_oneclick_ask(session)

    if existing_record:
        # Update the existing record
        existing_record = existing_record[0]
        update_data = {"declined": declined}
        session.update(existing_record, update_data)  # Use the session's update method
        session.commit()  # Commit the changes
        return existing_record  # Return the updated record
    else:
        # Create a new record using session's create method
        new_record_data = {"user_id": user_id, "declined": declined}
        new_record = session.create(OneclickAsk, new_record_data)  # Use create method
        session.commit()  # Commit the new record
        return new_record  # Return the newly created record
