from sqlalchemy.future import select
from fastapi import status
from repository.exceptions import request_exception


# def get_model_instance(get_function, *args, session: SessionDAL):
#     model_instance = None
#     flag = False
#     for val in args:
#         if val:
#             flag = True
#             break
#     if flag:
#         model_instance = get_function(*args, session)
#         if not model_instance:
#             raise request_exception(
#                 detail="Object does not exist", status_code=status.HTTP_404_NOT_FOUND
#             )

#     return model_instance


# # Obtiene una instancia de un modelo a partir del nombre del modelo, y la llave primaria
# # y una session.
# def get_model_instance_by_id(model: BaseMixin, primary_key_val, session: SessionDAL):
#     def get_function(id, session):
#         return session.get_by_id(select(model), model, id)

#     return get_model_instance(get_function, primary_key_val, session=session)


# def get_model_instance_by_id_in_form(
#     model: BaseMixin, model_form: OrmBaseModel, session: SessionDAL, primary_key_name
# ):
#     primary_key_val = model_form.model_dump().get(primary_key_name)
#     return get_model_instance_by_id(model, primary_key_val, session)


# def verify_condition(
#     verification_function,
#     *fargs,
#     status_code=status.HTTP_400_BAD_REQUEST,
#     detail="Bad request",
# ):
#     if not verification_function(*fargs):
#         raise request_exception(status_code=status_code, detail=detail)
